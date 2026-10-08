import asyncio
import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app import agent, briefings, scheduler
from app.core import db, events
from app.core.config import settings
from app.services.llm_service import LLMError, llm
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.tools import memory, reminders, research

logger = logging.getLogger(__name__)

router = APIRouter()

# Set by main.py
stt_service: Optional[STTService] = None
tts_service: Optional[TTSService] = None


class TTSRequest(BaseModel):
    text: str = Field(..., max_length=8000)
    voice: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=8000)
    voice: bool = False


class ReminderRequest(BaseModel):
    text: str
    when: str
    recurrence: str = "none"


class NoteRequest(BaseModel):
    title: str
    content: str
    tags: str = ""


class PrefsRequest(BaseModel):
    language: Optional[str] = None
    voice_es: Optional[str] = None
    voice_en: Optional[str] = None
    effect: Optional[str] = None


class ResearchRequest(BaseModel):
    prompt: str = Field(..., max_length=8000)


# ---- status ----------------------------------------------------------------

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "stt": bool(stt_service and stt_service.is_ready),
            "tts": bool(tts_service and tts_service.is_ready),
            "llm": llm.is_available,
            "research": research.claude_available(),
        },
    }


@router.get("/services/status")
async def get_services_status():
    return {
        "stt": stt_service.get_info() if stt_service else {"status": "not initialized"},
        "tts": tts_service.get_info() if tts_service else {"status": "not initialized"},
        "llm": llm.get_info(),
        "research": {"status": "ready" if research.claude_available() else "not available"},
        "jobs": scheduler.jobs_info(),
    }


@router.get("/llm/models")
async def llm_models():
    try:
        return {"models": await llm.list_models(), "current": llm.model}
    except Exception as e:
        raise HTTPException(502, f"No pude listar modelos: {e}")


# ---- voice -----------------------------------------------------------------

async def _transcribe(audio_file: UploadFile) -> str:
    if not stt_service or not stt_service.is_ready:
        raise HTTPException(503, "STT service not available")
    suffix = os.path.splitext(audio_file.filename or "")[1] or ".webm"
    lang = db.language()
    return await stt_service.transcribe_bytes(await audio_file.read(), suffix, None if lang == "auto" else lang)


@router.post("/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    text = await _transcribe(audio_file)
    if not text:
        raise HTTPException(400, "Could not transcribe audio")
    return {"text": text, "success": True}


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    if not tts_service or not tts_service.is_ready:
        raise HTTPException(503, "TTS service not available")
    path = await tts_service.synthesize(request.text, request.voice)
    if not path or not os.path.exists(path):
        raise HTTPException(500, "Failed to generate audio")
    media = "audio/mpeg" if path.endswith(".mp3") else "audio/wav"
    return FileResponse(path, media_type=media, filename=os.path.basename(path))


@router.get("/voices")
async def voices():
    return {"voices": tts_service.get_available_voices() if tts_service else []}


@router.get("/prefs")
async def get_prefs():
    return db.get_prefs()


@router.put("/prefs")
async def put_prefs(req: PrefsRequest):
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    if changes.get("language") not in (None, "es", "en", "auto"):
        raise HTTPException(400, "language must be es, en or auto")
    return db.set_prefs(changes)


@router.get("/identity")
async def identity():
    return {"name": settings.NAME, "user": settings.USER_NAME, "title": settings.USER_TITLE,
            "location": settings.LOCATION_LABEL, "timezone": settings.TIMEZONE,
            "cities": list(settings.LOCATIONS)}


# ---- conversation ----------------------------------------------------------

async def _run_agent(text: str, voice: bool) -> dict:
    if not llm.is_available:
        raise HTTPException(503, "LLM no configurado: falta TOTALGPT_API_KEY en .env")
    try:
        return await agent.run(text, voice=voice)
    except LLMError as e:
        raise HTTPException(502, str(e))


@router.post("/chat")
async def chat(request: ChatRequest):
    result = await _run_agent(request.message, request.voice)
    return {"user_text": request.message, "assistant_text": result["text"], "tools": result["tools"]}


@router.post("/conversation")
async def conversation(audio_file: UploadFile = File(...),
                       conversation_history: str = Form(default="[]")):
    """Voice turn: STT -> agent. The client fetches /tts for the audio.
    conversation_history is accepted for old clients but history now lives on the server."""
    user_text = await _transcribe(audio_file)
    if not user_text:
        raise HTTPException(400, "Could not transcribe audio")
    result = await _run_agent(user_text, voice=True)
    return {"user_text": user_text, "assistant_text": result["text"], "tools": result["tools"], "success": True}


@router.get("/messages")
async def messages(limit: int = 50):
    rows = db.recent_messages(limit)
    for r in rows:
        r["meta"] = json.loads(r["meta"]) if r["meta"] else None
    return {"messages": rows}


@router.delete("/messages")
async def clear_messages():
    db.execute("DELETE FROM messages")
    return {"cleared": True}


# ---- feed / briefings ------------------------------------------------------

@router.get("/feed")
async def feed(limit: int = 30, kind: Optional[str] = None):
    if kind:
        rows = db.query("SELECT * FROM feed WHERE kind = ? ORDER BY id DESC LIMIT ?", (kind, limit))
    else:
        rows = db.query("SELECT * FROM feed ORDER BY id DESC LIMIT ?", (limit,))
    unread = db.query_one("SELECT COUNT(*) AS n FROM feed WHERE read = 0")["n"]
    return {"items": rows, "unread": unread}


@router.post("/feed/read")
async def mark_feed_read():
    db.execute("UPDATE feed SET read = 1 WHERE read = 0")
    return {"ok": True}


@router.post("/briefings/{job}/run")
async def run_briefing(job: str):
    fn = briefings.JOBS.get(job)
    if not fn:
        raise HTTPException(404, f"Unknown briefing. Options: {list(briefings.JOBS)}")
    return await fn()


# ---- reminders -------------------------------------------------------------

@router.get("/reminders")
async def get_reminders(include_done: bool = False):
    return await reminders.list_reminders(include_done)


@router.post("/reminders")
async def add_reminder(req: ReminderRequest):
    result = await reminders.create_reminder(req.text, req.when, req.recurrence)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.delete("/reminders/{rid}")
async def done_reminder(rid: int):
    return await reminders.complete_reminder(rid)


# ---- memory notes ----------------------------------------------------------

@router.get("/notes")
async def list_notes():
    return {"notes": [{k: n[k] for k in ("slug", "title", "tags", "links", "updated_at")}
                      for n in memory.all_notes()]}


@router.get("/notes/{slug}")
async def get_note(slug: str):
    note = memory.read_note(slug)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@router.put("/notes")
async def put_note(req: NoteRequest):
    return memory.write_note(req.title, req.content, req.tags)


# ---- deep research ---------------------------------------------------------

@router.get("/research")
async def list_research(limit: int = 30):
    return {"jobs": db.query("SELECT id, prompt, status, error, cost_usd, created_at, finished_at "
                             "FROM research ORDER BY id DESC LIMIT ?", (limit,))}


@router.get("/research/{job_id}")
async def get_research(job_id: int):
    row = db.query_one("SELECT * FROM research WHERE id = ?", (job_id,))
    if not row:
        raise HTTPException(404, "Research job not found")
    return row


@router.post("/research")
async def create_research(req: ResearchRequest):
    result = await research.deep_research(req.prompt)
    if "error" in result:
        raise HTTPException(503, result["error"])
    return result


# ---- live events (SSE) -----------------------------------------------------

@router.get("/events")
async def event_stream(request: Request):
    q = events.subscribe()

    async def gen():
        try:
            yield "event: hello\ndata: {}\n\n"
            while not await request.is_disconnected():
                try:
                    yield await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            events.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
