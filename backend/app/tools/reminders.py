"""Reminders stored in SQLite and fired by the scheduler."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core import db
from app.core.config import settings

RECURRENCES = ("none", "daily", "weekdays", "weekly")


def _tz():
    return ZoneInfo(settings.TIMEZONE)


def parse_when(when: str) -> datetime:
    dt = datetime.fromisoformat(when.strip().replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=_tz())


def next_occurrence(due: datetime, recurrence: str) -> datetime:
    now = datetime.now(_tz())
    step = {"daily": 1, "weekdays": 1, "weekly": 7}[recurrence]
    nxt = due
    while nxt <= now or (recurrence == "weekdays" and nxt.weekday() >= 5):
        nxt += timedelta(days=step)
    return nxt


async def create_reminder(text: str, when: str, recurrence: str = "none") -> dict:
    if recurrence not in RECURRENCES:
        recurrence = "none"
    try:
        due = parse_when(when)
    except ValueError:
        return {"error": "Formato de fecha inválido. Usa ISO 8601, p. ej. 2026-10-06T15:30"}
    rid = db.execute(
        "INSERT INTO reminders (text, due_at, recurrence, created_at) VALUES (?, ?, ?, ?)",
        (text, due.isoformat(timespec="seconds"), recurrence, db.now_iso()),
    )
    return {"id": rid, "text": text, "due_at": due.isoformat(timespec="minutes"), "recurrence": recurrence}


async def list_reminders(include_done: bool = False) -> dict:
    sql = "SELECT * FROM reminders" + ("" if include_done else " WHERE done = 0") + " ORDER BY due_at"
    return {"reminders": db.query(sql)}


async def complete_reminder(id: int) -> dict:
    db.execute("UPDATE reminders SET done = 1 WHERE id = ?", (id,))
    return {"done": id}


def due_reminders() -> list:
    """Reminders whose time has come. Recurring ones are rescheduled, others marked done."""
    now = datetime.now(_tz())
    fired = []
    for r in db.query("SELECT * FROM reminders WHERE done = 0"):
        due = parse_when(r["due_at"])
        if due > now:
            continue
        if r["recurrence"] == "none":
            db.execute("UPDATE reminders SET done = 1, last_fired_at = ? WHERE id = ?", (db.now_iso(), r["id"]))
        else:
            nxt = next_occurrence(due, r["recurrence"])
            db.execute("UPDATE reminders SET due_at = ?, last_fired_at = ? WHERE id = ?",
                       (nxt.isoformat(timespec="seconds"), db.now_iso(), r["id"]))
        fired.append(r)
    return fired


TOOLS = [
    {
        "name": "create_reminder",
        "description": "Crea un recordatorio. Calcula la fecha/hora exacta a partir de la hora actual.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Qué recordar"},
                "when": {"type": "string", "description": "Fecha y hora local ISO 8601, p. ej. 2026-10-06T15:30"},
                "recurrence": {"type": "string", "enum": list(RECURRENCES)},
            },
            "required": ["text", "when"],
        },
        "handler": create_reminder,
    },
    {
        "name": "list_reminders",
        "description": "Lista recordatorios pendientes.",
        "parameters": {"type": "object", "properties": {"include_done": {"type": "boolean"}}},
        "handler": list_reminders,
    },
    {
        "name": "complete_reminder",
        "description": "Marca un recordatorio como hecho.",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
        "handler": complete_reminder,
    },
]
