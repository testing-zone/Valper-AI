import asyncio
import logging
import re
import tempfile
import time
from typing import Optional

import httpx

from app.core import db
from app.core.config import settings

logger = logging.getLogger(__name__)

# Curated presets (blends). Kokoro picks pronunciation from the first voice's prefix,
# so a preset must stay within one language.
PRESETS = [
    ("em_alex(2)+em_santa(1)", "Mayordomo", "es", "m"),
    ("em_santa(2)+em_alex(1)", "Grave", "es", "m"),
    ("bm_george(2)+bm_fable(1)", "Butler", "en-GB", "m"),
    ("bm_george(2)+am_onyx(1)", "Colossus", "en-GB", "m"),
    ("bm_fable(2)+bm_daniel(1)", "Narrator", "en-GB", "m"),
    ("am_onyx(2)+am_fenrir(1)", "Deep", "en-US", "m"),
]

# Kokoro v1.0 catalog. Voices can be blended: "em_santa(2)+am_onyx(1)"
VOICES = [
    ("em_santa", "Santa", "es", "m"), ("em_alex", "Alex", "es", "m"), ("ef_dora", "Dora", "es", "f"),
    ("am_onyx", "Onyx", "en-US", "m"), ("am_fenrir", "Fenrir", "en-US", "m"), ("am_echo", "Echo", "en-US", "m"),
    ("am_eric", "Eric", "en-US", "m"), ("am_liam", "Liam", "en-US", "m"), ("am_michael", "Michael", "en-US", "m"),
    ("am_adam", "Adam", "en-US", "m"), ("am_puck", "Puck", "en-US", "m"), ("am_santa", "Santa", "en-US", "m"),
    ("af_heart", "Heart", "en-US", "f"), ("af_bella", "Bella", "en-US", "f"), ("af_nicole", "Nicole", "en-US", "f"),
    ("af_nova", "Nova", "en-US", "f"), ("af_sky", "Sky", "en-US", "f"), ("af_sarah", "Sarah", "en-US", "f"),
    ("af_alloy", "Alloy", "en-US", "f"), ("af_aoede", "Aoede", "en-US", "f"), ("af_jessica", "Jessica", "en-US", "f"),
    ("af_kore", "Kore", "en-US", "f"), ("af_river", "River", "en-US", "f"),
    ("bm_george", "George", "en-GB", "m"), ("bm_fable", "Fable", "en-GB", "m"), ("bm_daniel", "Daniel", "en-GB", "m"),
    ("bm_lewis", "Lewis", "en-GB", "m"), ("bf_emma", "Emma", "en-GB", "f"), ("bf_isabella", "Isabella", "en-GB", "f"),
    ("bf_alice", "Alice", "en-GB", "f"), ("bf_lily", "Lily", "en-GB", "f"),
    ("pm_alex", "Alex", "pt-BR", "m"), ("pm_santa", "Santa", "pt-BR", "m"), ("pf_dora", "Dora", "pt-BR", "f"),
    ("im_nicola", "Nicola", "it", "m"), ("if_sara", "Sara", "it", "f"), ("ff_siwis", "Siwis", "fr", "f"),
    ("jm_kumo", "Kumo", "ja", "m"), ("jf_alpha", "Alpha", "ja", "f"), ("jf_nebula", "Nebula", "ja", "f"),
    ("zm_yunjian", "Yunjian", "zh", "m"), ("zf_xiaoxiao", "Xiaoxiao", "zh", "f"),
    ("hm_omega", "Omega", "hi", "m"), ("hf_alpha", "Alpha", "hi", "f"),
]


SPANISH_HINTS = re.compile(r"\b(el|la|los|las|que|de|y|en|un|una|es|por|con|para|hay|está|tienes|qué)\b", re.I)
ENGLISH_HINTS = re.compile(r"\b(the|and|is|are|you|to|of|in|it|that|for|with|have|there|what)\b", re.I)


def detect_language(text: str) -> str:
    return "en" if len(ENGLISH_HINTS.findall(text)) > len(SPANISH_HINTS.findall(text)) else "es"


def clean_for_speech(text: str) -> str:
    """Strip markdown, links and URLs so the voice doesn't read symbols."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"[*_`#>|]+", "", text)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{2,}", ". ", text).strip()


class TTSService:
    """Text-to-speech with Kokoro, hosted on TotalGPT/Infermatic or running locally."""

    def __init__(self):
        self.provider = settings.TTS_PROVIDER
        self.pipeline = None
        self.is_ready = False
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=60)
        self.last_latency_ms: Optional[int] = None

    async def initialize(self):
        if self.provider == "infermatic":
            self.is_ready = bool(settings.LLM_API_KEY)
            logger.info(f"TTS via Infermatic ({settings.TTS_MODEL}), ready={self.is_ready}")
            return
        try:
            logger.info(f"Loading local Kokoro TTS pipeline (lang={settings.TTS_LANG})...")
            from kokoro import KPipeline
            self.pipeline = await asyncio.to_thread(KPipeline, lang_code=settings.TTS_LANG)
            self.is_ready = True
        except Exception as e:
            logger.error(f"Error initializing Kokoro TTS: {e}")
            self.is_ready = False

    def _out_path(self, suffix: str) -> str:
        settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        out = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=settings.AUDIO_DIR)
        out.close()
        return out.name

    async def _synthesize_remote(self, text: str, voice: str) -> Optional[str]:
        resp = await self._client.post(
            f"{settings.LLM_BASE_URL.rstrip('/')}/audio/speech",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
            json={"model": settings.TTS_MODEL, "input": text, "voice": voice, "response_format": "mp3"},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Infermatic TTS {resp.status_code} (voz '{voice}'?): {resp.text[:200]}")
        path = self._out_path(".mp3")
        with open(path, "wb") as f:
            f.write(resp.content)
        return path

    def _synthesize_local(self, text: str, voice: str) -> Optional[str]:
        import numpy as np
        import soundfile as sf

        parts = [audio for _, _, audio in self.pipeline(text, voice=voice, split_pattern=r"\n+|(?<=[.!?])\s+")]
        if not parts:
            return None
        path = self._out_path(".wav")
        sf.write(path, np.concatenate(parts), 24000)
        return path

    async def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[str]:
        """Returns the path to an audio file (.mp3 remote, .wav local)."""
        if not self.is_ready:
            raise RuntimeError("TTS service not initialized")
        text = clean_for_speech(text)
        if not text:
            return None
        if not voice:
            prefs = db.get_prefs()
            lang = detect_language(text) if prefs["language"] == "auto" else prefs["language"]
            voice = prefs[f"voice_{lang}"]
        start = time.monotonic()
        try:
            if self.provider == "infermatic":
                path = await self._synthesize_remote(text, voice)
            else:
                async with self._lock:  # local Kokoro pipeline is not thread-safe
                    path = await asyncio.to_thread(self._synthesize_local, text, voice)
            self.last_latency_ms = int((time.monotonic() - start) * 1000)
            return path
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None

    synthesize_speech = synthesize

    def get_available_voices(self) -> list:
        presets = [{"id": v, "name": n, "lang": l, "gender": g, "preset": True} for v, n, l, g in PRESETS]
        return presets + [{"id": v, "name": n, "lang": l, "gender": g} for v, n, l, g in VOICES]

    def is_available(self) -> bool:
        return self.is_ready

    def get_info(self) -> dict:
        return {
            "service": f"Kokoro ({self.provider})",
            "status": "ready" if self.is_ready else "not available",
            "voice": db.voice_for("es" if db.language() == "auto" else None),
            "latency_ms": self.last_latency_ms,
        }
