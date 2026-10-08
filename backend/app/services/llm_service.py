"""LLM client for TotalGPT (OpenAI-compatible chat completions API).

Supports two ways of calling tools:
- native: OpenAI `tools` / `tool_calls` (if the hosted model supports it)
- prompt: Hermes-style <tool_call>{...}</tool_call> tags in plain text, which
  works with almost any instruction-tuned model (Qwen, Llama, Mistral...)
In `auto` mode we try native first and fall back to prompt mode on error.
"""
import asyncio
import json
import logging
import re
import time
import uuid
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)


def strip_reasoning(text: str) -> str:
    """Remove Qwen3 reasoning. When the server doesn't split it out, the visible text
    is `<reasoning>...</think>answer` (the opening tag lives in the prompt)."""
    text = THINK_RE.sub("", text)
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    return text.strip()


class LLMError(Exception):
    pass


class LLMService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL
        self.tool_mode = settings.LLM_TOOL_MODE  # auto | native | prompt
        self._client = httpx.AsyncClient(timeout=settings.LLM_TIMEOUT)
        self.last_latency_ms: Optional[int] = None

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def is_ready(self) -> bool:
        return self.is_available

    async def _post(self, payload: dict, think: bool = False) -> dict:
        if not self.api_key:
            raise LLMError("TOTALGPT_API_KEY no está configurada")
        payload = {**payload, "chat_template_kwargs": {"enable_thinking": think or settings.LLM_THINKING}}
        start = time.monotonic()
        for attempt in range(4):
            resp = await self._client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            if resp.status_code != 429 or attempt == 3:
                break
            # TotalGPT rate limit (requests/minute): back off and retry
            wait = 4 * (attempt + 1)
            logger.warning(f"TotalGPT rate limit hit, retrying in {wait}s")
            await asyncio.sleep(wait)
        if resp.status_code != 200:
            raise LLMError(f"TotalGPT {resp.status_code}: {resp.text[:500]}")
        self.last_latency_ms = int((time.monotonic() - start) * 1000)
        return resp.json()

    async def list_models(self) -> List[str]:
        resp = await self._client.get(
            f"{self.base_url}/models", headers={"Authorization": f"Bearer {self.api_key}"}
        )
        resp.raise_for_status()
        return [m["id"] for m in resp.json().get("data", [])]

    async def complete(self, messages: List[Dict], model: Optional[str] = None,
                       max_tokens: int = 1500, temperature: float = 0.6) -> str:
        """Plain completion without tools."""
        data = await self._post({
            "model": model or self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })
        return THINK_RE.sub("", data["choices"][0]["message"].get("content") or "").strip()

    async def chat_with_tools(self, messages: List[Dict], tools: List[Dict], max_tokens: int = 1500,
                              require_tool: bool = False, think: bool = False) -> Dict:
        """One model turn. Returns {"content": str, "tool_calls": [{"id","name","arguments"}]}.

        `messages` uses the OpenAI format, including assistant messages with
        `tool_calls` and `tool` role results; prompt mode converts them.
        """
        if self.tool_mode in ("auto", "native"):
            try:
                return await self._native_turn(messages, tools, max_tokens, require_tool, think)
            except LLMError as e:
                # only fall back when the server rejects tool calling itself, not on rate limits etc.
                if self.tool_mode == "native" or "tool" not in str(e).lower():
                    raise
                logger.warning(f"Native tool calling failed, switching to prompt mode: {e}")
                self.tool_mode = "prompt"
        return await self._prompt_turn(messages, tools, max_tokens)

    async def _native_turn(self, messages, tools, max_tokens, require_tool=False, think=False) -> Dict:
        data = await self._post({
            "model": self.model,
            "messages": messages,
            "tools": [{"type": "function", "function": t} for t in tools],
            "tool_choice": "required" if require_tool else "auto",
            "max_tokens": 700 if think else max_tokens,  # cap reasoning; truncated -> agent retries plain
            "temperature": 0.5,
        }, think=think)
        msg = data["choices"][0]["message"]
        calls = []
        for tc in msg.get("tool_calls") or []:
            args = tc["function"].get("arguments") or "{}"
            try:
                args = json.loads(args) if isinstance(args, str) else args
            except json.JSONDecodeError:
                args = {}
            calls.append({"id": tc.get("id") or uuid.uuid4().hex[:8],
                          "name": tc["function"]["name"], "arguments": args})
        raw = msg.get("content") or ""
        content = strip_reasoning(raw)
        if think and (calls or "</think>" not in raw):
            content = ""  # only reasoning (tool turn, or truncated before the answer)
        # Some servers accept `tools` but the model still writes tags in text
        if not calls:
            content, calls = self._parse_tagged_calls(content)
        return {"content": content.strip(), "tool_calls": calls}

    async def _prompt_turn(self, messages, tools, max_tokens) -> Dict:
        converted = self._to_prompt_messages(messages, tools)
        data = await self._post({
            "model": self.model,
            "messages": converted,
            "max_tokens": max_tokens,
            "temperature": 0.5,
            "stop": ["<tool_response>"],
        })
        content = THINK_RE.sub("", data["choices"][0]["message"].get("content") or "")
        content, calls = self._parse_tagged_calls(content)
        return {"content": content.strip(), "tool_calls": calls}

    @staticmethod
    def _parse_tagged_calls(content: str):
        calls = []
        for match in TOOL_CALL_RE.finditer(content):
            try:
                obj = json.loads(match.group(1))
                calls.append({"id": uuid.uuid4().hex[:8], "name": obj["name"],
                              "arguments": obj.get("arguments") or {}})
            except (json.JSONDecodeError, KeyError):
                logger.warning(f"Unparseable tool call: {match.group(1)[:200]}")
        return TOOL_CALL_RE.sub("", content), calls

    @staticmethod
    def _to_prompt_messages(messages: List[Dict], tools: List[Dict]) -> List[Dict]:
        tool_doc = (
            "\n\n# Herramientas\nTienes acceso a estas funciones (JSON schema):\n<tools>\n"
            + "\n".join(json.dumps(t, ensure_ascii=False) for t in tools)
            + "\n</tools>\n\nPara llamar una función responde SOLO con:\n"
            '<tool_call>{"name": "<nombre>", "arguments": {...}}</tool_call>\n'
            "Puedes hacer varias llamadas seguidas. Los resultados llegan en <tool_response>. "
            "Cuando tengas lo necesario, responde normalmente sin etiquetas."
        )
        out = []
        for m in messages:
            role = m["role"]
            if role == "system":
                out.append({"role": "system", "content": m["content"] + tool_doc})
            elif role == "assistant" and m.get("tool_calls"):
                text = m.get("content") or ""
                for tc in m["tool_calls"]:
                    fn = tc["function"]
                    args = fn["arguments"] if isinstance(fn["arguments"], str) else json.dumps(fn["arguments"])
                    text += f'\n<tool_call>{{"name": "{fn["name"]}", "arguments": {args}}}</tool_call>'
                out.append({"role": "assistant", "content": text.strip()})
            elif role == "tool":
                block = f"<tool_response name=\"{m.get('name', '')}\">\n{m['content']}\n</tool_response>"
                # merge consecutive tool results into a single user turn
                if out and out[-1]["role"] == "user" and out[-1]["content"].startswith("<tool_response"):
                    out[-1]["content"] += "\n" + block
                else:
                    out.append({"role": "user", "content": block})
            else:
                out.append({"role": role, "content": m["content"]})
        return out

    def get_info(self) -> Dict:
        return {
            "service": "TotalGPT",
            "model": self.model,
            "tool_mode": self.tool_mode,
            "status": "ready" if self.is_available else "not available",
            "api_configured": bool(self.api_key),
            "latency_ms": self.last_latency_ms,
        }


llm = LLMService()
