"""A plain to-do list: things to do, optionally for a given day (no alarm, unlike reminders)."""
from datetime import date

from app.core import db


async def add_task(text: str, due: str = "") -> dict:
    tid = db.execute("INSERT INTO tasks (text, due, created_at) VALUES (?, ?, ?)",
                     (text.strip(), due.strip()[:10] or None, db.now_iso()))
    return {"id": tid, "text": text, "due": due or None}


async def list_tasks(include_done: bool = False) -> dict:
    sql = "SELECT id, text, due, done FROM tasks" + ("" if include_done else " WHERE done = 0")
    return {"tasks": db.query(sql + " ORDER BY due IS NULL, due, id"), "today": date.today().isoformat()}


async def complete_task(id: int) -> dict:
    db.execute("UPDATE tasks SET done = 1, done_at = ? WHERE id = ?", (db.now_iso(), id))
    return {"done": id}


def open_tasks() -> list:
    return db.query("SELECT id, text, due FROM tasks WHERE done = 0 ORDER BY due IS NULL, due, id LIMIT 15")


TOOLS = [
    {
        "name": "add_task",
        "description": "Agrega una tarea a la lista de pendientes ('tengo que…', 'agrega a mis tareas…'). "
                       "Para avisos a una hora exacta usa create_reminder.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string"},
            "due": {"type": "string", "description": "Fecha opcional YYYY-MM-DD"}}, "required": ["text"]},
        "handler": add_task,
    },
    {
        "name": "list_tasks",
        "description": "Lista las tareas pendientes.",
        "parameters": {"type": "object", "properties": {"include_done": {"type": "boolean"}}},
        "handler": list_tasks,
    },
    {
        "name": "complete_task",
        "description": "Marca una tarea como hecha.",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
        "handler": complete_task,
    },
]
