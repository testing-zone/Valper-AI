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
    return settings.ORCA_BIN or shutil.which("orca") or APP_CLI


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
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text[-4000:]}


async def is_running() -> bool:
    try:
        status = await run("status", timeout=10)
    except Exception:
        return False
    return bool(status.get("runtimeReachable") or status.get("appRunning")) if isinstance(status, dict) else False


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
