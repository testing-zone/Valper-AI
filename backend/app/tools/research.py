"""Deep research delegated to Claude Code running headless (`claude -p`).

Talos queues a job, Claude Code researches with web search in its own
working folder, and the final markdown report lands in the UI (Investigación tab).
"""
import asyncio
import json
import logging
import os
import shutil

from app.core import db, events
from app.core.config import settings
from app.tools import notify

logger = logging.getLogger(__name__)

SYSTEM = (
    "Eres el módulo de investigación profunda de un asistente personal. Investiga a fondo usando "
    "búsqueda web, contrasta fuentes y entrega un reporte final en español, en markdown: "
    "un resumen de 3-5 líneas al inicio, luego hallazgos con detalle y al final la lista de fuentes con URLs. "
    "Tu respuesta final ES el reporte; no preguntes nada al usuario."
)

_running: dict = {}


def claude_available() -> bool:
    return shutil.which(settings.CLAUDE_BIN) is not None


async def _run(job_id: int, prompt: str):
    workdir = settings.RESEARCH_DIR / str(job_id)
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        settings.CLAUDE_BIN, "-p", prompt,
        "--output-format", "json",
        "--allowedTools", settings.RESEARCH_TOOLS,
        "--append-system-prompt", SYSTEM,
    ]
    if settings.CLAUDE_MODEL:
        cmd += ["--model", settings.CLAUDE_MODEL]

    db.execute("UPDATE research SET status = 'running' WHERE id = ?", (job_id,))
    events.publish("research", {"id": job_id, "status": "running"})
    try:
        env = dict(os.environ)
        if settings.CLAUDE_USE_SUBSCRIPTION:
            env.pop("ANTHROPIC_API_KEY", None)
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=workdir, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=settings.RESEARCH_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"Tiempo agotado ({settings.RESEARCH_TIMEOUT}s)")

        if proc.returncode != 0 and not out:
            raise RuntimeError(err.decode(errors="ignore")[-1500:] or f"exit {proc.returncode}")
        data = json.loads(out.decode())
        if data.get("is_error"):
            raise RuntimeError(str(data.get("result") or data)[:1500])

        report = data.get("result", "")
        (workdir / "reporte.md").write_text(report, encoding="utf-8")
        db.execute(
            "UPDATE research SET status = 'done', result = ?, cost_usd = ?, finished_at = ? WHERE id = ?",
            (report, data.get("total_cost_usd"), db.now_iso(), job_id),
        )
        events.publish("research", {"id": job_id, "status": "done"})
        summary = report.strip().split("\n\n")[0][:400]
        await notify.push("research", f"Investigación lista: {prompt[:60]}", summary,
                          {"research_id": job_id})
    except Exception as e:
        logger.error(f"Research job {job_id} failed: {e}")
        db.execute("UPDATE research SET status = 'error', error = ?, finished_at = ? WHERE id = ?",
                   (str(e), db.now_iso(), job_id))
        events.publish("research", {"id": job_id, "status": "error", "error": str(e)})
    finally:
        _running.pop(job_id, None)


def start_research(prompt: str) -> int:
    job_id = db.execute(
        "INSERT INTO research (prompt, status, created_at) VALUES (?, 'queued', ?)",
        (prompt, db.now_iso()),
    )
    _running[job_id] = asyncio.create_task(_run(job_id, prompt))
    events.publish("research", {"id": job_id, "status": "queued", "prompt": prompt})
    return job_id


async def deep_research(prompt: str) -> dict:
    if not claude_available():
        return {"error": f"No encuentro '{settings.CLAUDE_BIN}'. Configura CLAUDE_BIN en .env."}
    job_id = start_research(prompt)
    return {"job_id": job_id, "status": "queued",
            "note": "Corre en segundo plano (puede tardar varios minutos). El reporte aparecerá en Investigación."}


async def research_status(job_id: int) -> dict:
    row = db.query_one("SELECT id, prompt, status, error, created_at, finished_at FROM research WHERE id = ?",
                       (job_id,))
    return row or {"error": "No existe ese trabajo"}


TOOLS = [
    {
        "name": "deep_research",
        "description": "Lanza una investigación profunda en internet con Claude Code (tarda minutos, corre en "
                       "segundo plano). Úsalo para preguntas que requieren buscar, comparar y leer muchas "
                       "fuentes. Escribe un prompt completo y específico.",
        "parameters": {
            "type": "object",
            "properties": {"prompt": {"type": "string", "description": "Qué investigar, con todo el contexto"}},
            "required": ["prompt"],
        },
        "handler": deep_research,
    },
    {
        "name": "research_status",
        "description": "Estado de una investigación lanzada.",
        "parameters": {"type": "object", "properties": {"job_id": {"type": "integer"}}, "required": ["job_id"]},
        "handler": research_status,
    },
]
