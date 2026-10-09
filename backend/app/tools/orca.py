"""Orca (Stably AI) integration — read-only for now: what are my coding agents doing?

Uses the `orca` CLI that ships inside Orca.app; every command supports --json.
Orca must be open (or `orca serve` running) for the runtime to answer.
"""
import asyncio
import json
import logging
import shutil

from app.core.config import settings

logger = logging.getLogger(__name__)

APP_CLI = "/Applications/Orca.app/Contents/Resources/bin/orca"


def cli() -> str:
    # prefer the CLI inside the app bundle: the /usr/local/bin/orca symlink can be broken after updates
    if settings.ORCA_BIN:
        return settings.ORCA_BIN
    import os
    return APP_CLI if os.path.exists(APP_CLI) else (shutil.which("orca") or APP_CLI)


def available() -> bool:
    return bool(shutil.which(cli()))


async def run(*args: str, timeout: int = 20):
    """Run an orca command with --json. Returns parsed JSON, or {"text": ...} if not JSON."""
    proc = await asyncio.create_subprocess_exec(
        cli(), *args, "--json", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"orca {' '.join(args)}: sin respuesta en {timeout}s")
    text = out.decode(errors="ignore").strip()
    if proc.returncode != 0 and not text:
        raise RuntimeError(err.decode(errors="ignore").strip()[-400:] or f"exit {proc.returncode}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"text": text[-4000:]}
    # every orca command answers {"id", "ok", "result": {...}}
    if isinstance(data, dict) and "result" in data:
        if data.get("ok") is False:
            raise RuntimeError(str(data.get("error"))[:400])
        return data["result"]
    return data


async def is_running() -> bool:
    try:
        status = await run("status", timeout=10)
    except Exception:
        return False
    if not isinstance(status, dict):
        return False
    return bool((status.get("runtime") or {}).get("reachable") or status.get("runtimeReachable"))


async def orca_agents(limit: int = 20) -> dict:
    """Snapshot of Orca worktrees and their agents, for the model to summarize."""
    if not available():
        return {"error": "No encuentro el CLI de Orca. ¿Está instalado Orca.app?"}
    if not await is_running():
        return {"error": "Orca está cerrado. Ábrelo (o corre `orca serve`) para ver los agentes."}
    data = {}
    try:
        data["worktrees"] = await run("worktree", "ps", "--limit", str(limit))
    except Exception as e:
        data["worktrees_error"] = str(e)
    try:
        data["terminals"] = await run("terminal", "list", "--limit", str(limit))
    except Exception as e:
        data["terminals_error"] = str(e)
    return data


async def orca_terminal_output(terminal: str, lines: int = 60) -> dict:
    """Last rendered screen of one agent terminal, to see what it is doing or asking."""
    if not await is_running():
        return {"error": "Orca está cerrado."}
    return await run("terminal", "read", "--terminal", terminal, "--screen", "--limit", str(lines * 200))


TOOLS = [
    {
        "name": "orca_agents",
        "description": "Estado de los agentes de código en Orca (worktrees, terminales, qué está haciendo cada "
                       "agente, cuáles terminaron o esperan respuesta). Úsalo para '¿qué están haciendo mis "
                       "agentes?', '¿ya terminó X?'. Resume en una línea por agente.",
        "parameters": {"type": "object", "properties": {}},
        "handler": orca_agents,
    },
    {
        "name": "orca_terminal_output",
        "description": "Lee la pantalla actual de la terminal de un agente en Orca (por su handle, de orca_agents) "
                       "para ver en qué va o qué está preguntando.",
        "parameters": {"type": "object", "properties": {"terminal": {"type": "string"}},
                       "required": ["terminal"]},
        "handler": orca_terminal_output,
    },
]


# ---- watcher: alert when an agent finishes, needs you, or fails ---------------

NEEDS_YOU = ("blocked", "waiting", "permission", "awaiting")
FINISHED = ("done", "idle")
FAILED = ("error", "failed", "interrupted")
REMIND_AFTER = 15 * 60

_last: dict = {}  # paneKey -> (kind, since_ts, reminded, episode)
_primed = False


def _kind(state: str) -> str:
    s = (state or "").lower()
    if any(k in s for k in NEEDS_YOU):
        return "needs_you"
    if any(k in s for k in FAILED):
        return "failed"
    if any(k in s for k in FINISHED):
        return "finished"
    return "working"


def _where(w: dict) -> str:
    name = w.get("displayName") or w.get("branch", "").replace("refs/heads/", "")
    return f"{w.get('repo')}/{name}" if name and name != w.get("repo", "").lower() else str(w.get("repo"))


async def watch():
    """Scheduler job. First run only records current states, so old agents don't spam."""
    global _primed
    import time
    from app.core import db

    if not available() or not await is_running():
        return
    try:
        data = await run("worktree", "ps", "--limit", "50")
    except Exception as e:
        logger.debug(f"orca watch failed: {e}")
        return
    en = db.language() == "en"
    title_word = f"{settings.USER_TITLE}, " if settings.USER_TITLE else ""
    now = time.time()
    seen = set()
    for w in data.get("worktrees", []):
        for a in w.get("agents") or []:
            key = a.get("paneKey") or f"{w.get('worktreeId')}:{a.get('agentType')}"
            seen.add(key)
            kind = _kind(a.get("state"))
            # stateStartedAt changes on every new episode, so a task that went working -> done
            # between two polls still counts as a new completion
            episode = a.get("stateStartedAt") or (a.get("mainAgent") or {}).get("stateStartedAt")
            prev = _last.get(key)
            if prev and prev[0] == kind and prev[3] == episode:
                if kind == "needs_you" and not prev[2] and now - prev[1] > REMIND_AFTER:
                    _last[key] = (kind, prev[1], True, episode)
                    await _alert("needs_you", w, a, en, title_word, reminder=True)
                continue
            _last[key] = (kind, now, False, episode)
            if _primed and kind != "working":
                await _alert(kind, w, a, en, title_word)
    for key in list(_last):
        if key not in seen:
            _last.pop(key)
    _primed = True


async def _alert(kind: str, w: dict, a: dict, en: bool, title_word: str, reminder: bool = False):
    from app.tools import notify
    where = _where(w)
    task = (a.get("prompt") or a.get("taskTitle") or "").strip().replace("\n", " ")[:140]
    agent = a.get("agentType") or "agent"
    if kind == "finished":
        title = f"Orca · {agent} terminó en {where}"
        result = (a.get("lastAssistantMessage") or "").strip()[:900]
        body = f"**Tarea:** {task}\n\n{result}" if task else result
        speak = (f"{title_word}the {agent} agent in {where} has finished." if en
                 else f"{title_word}el agente de {where} terminó.")
    elif kind == "needs_you":
        title = f"Orca · {agent} te necesita en {where}" + (" (sigue esperando)" if reminder else "")
        screen = (w.get("preview") or "").strip()[-600:]
        body = f"**Tarea:** {task}\n\n```\n{screen}\n```" if screen else f"**Tarea:** {task}"
        speak = (f"{title_word}the agent in {where} is waiting for you." if en
                 else f"{title_word}el agente de {where} lo está esperando.")
    else:
        title = f"Orca · {agent} falló en {where}"
        body = f"**Tarea:** {task}\n\nEstado: {a.get('state')}"
        speak = (f"{title_word}the agent in {where} failed." if en
                 else f"{title_word}el agente de {where} falló.")
    await notify.push("orca", title, body, {"worktree": w.get("worktreeId"), "state": a.get("state")}, speak=speak)
