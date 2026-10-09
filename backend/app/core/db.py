"""SQLite persistence: conversation, feed (briefings), reminders, research jobs."""
import json
import sqlite3
import threading
from datetime import datetime
from typing import Optional

from app.core.config import settings

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    meta TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data TEXT,
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    due_at TEXT NOT NULL,
    recurrence TEXT NOT NULL DEFAULT 'none',
    done INTEGER NOT NULL DEFAULT 0,
    last_fired_at TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    error TEXT,
    cost_usd REAL,
    created_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    due TEXT,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    done_at TEXT
);
CREATE TABLE IF NOT EXISTS prefs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS articles (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT,
    category TEXT,
    text TEXT,
    fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS seen_items (
    url TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def init():
    global _conn
    settings.ensure_dirs()
    _conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.executescript(SCHEMA)
    _conn.commit()


def execute(sql: str, params: tuple = ()) -> int:
    with _lock:
        cur = _conn.execute(sql, params)
        _conn.commit()
        return cur.lastrowid


def query(sql: str, params: tuple = ()) -> list:
    with _lock:
        return [dict(r) for r in _conn.execute(sql, params).fetchall()]


def query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    rows = query(sql, params)
    return rows[0] if rows else None


# ---- messages -------------------------------------------------------------

def add_message(role: str, content: str, meta: Optional[dict] = None) -> int:
    return execute(
        "INSERT INTO messages (role, content, meta, created_at) VALUES (?, ?, ?, ?)",
        (role, content, json.dumps(meta) if meta else None, now_iso()),
    )


def recent_messages(limit: int = 20) -> list:
    rows = query("SELECT * FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    return list(reversed(rows))


# ---- feed -----------------------------------------------------------------

def add_feed(kind: str, title: str, body: str, data: Optional[dict] = None) -> dict:
    fid = execute(
        "INSERT INTO feed (kind, title, body, data, created_at) VALUES (?, ?, ?, ?, ?)",
        (kind, title, body, json.dumps(data, ensure_ascii=False) if data else None, now_iso()),
    )
    return query_one("SELECT * FROM feed WHERE id = ?", (fid,))


# ---- seen items (dedupe news across digests) ------------------------------

def filter_unseen(urls: list) -> set:
    """Return the subset of urls not seen before, and mark them as seen."""
    fresh = set()
    with _lock:
        for url in urls:
            if not _conn.execute("SELECT 1 FROM seen_items WHERE url = ?", (url,)).fetchone():
                fresh.add(url)
                _conn.execute("INSERT INTO seen_items (url, first_seen) VALUES (?, ?)", (url, now_iso()))
        _conn.commit()
    return fresh


# ---- user preferences (language, voices, audio effect) --------------------

def get_prefs() -> dict:
    prefs = {
        "language": settings.LANGUAGE,
        "voice_es": settings.TTS_VOICE_ES,
        "voice_en": settings.TTS_VOICE_EN,
        "effect": "none",
    }
    for row in query("SELECT key, value FROM prefs"):
        prefs[row["key"]] = json.loads(row["value"])
    return prefs


def set_prefs(changes: dict) -> dict:
    with _lock:
        for key, value in changes.items():
            _conn.execute("INSERT INTO prefs (key, value) VALUES (?, ?) "
                          "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, json.dumps(value)))
        _conn.commit()
    return get_prefs()


def language() -> str:
    return get_prefs()["language"]


def voice_for(lang: str = None) -> str:
    prefs = get_prefs()
    return prefs[f"voice_{lang or prefs['language']}"]
