"""Long-term memory as plain markdown notes (Obsidian-style).

Each note is data/memory/<slug>.md and can link to others with [[Título]].
`perfil.md` holds stable facts about the user and is injected into every prompt.
You can open the folder in Obsidian or any editor and edit notes by hand.
"""
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from app.core.config import settings

PROFILE_SLUG = "perfil"
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")


def slugify(title: str) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80] or "nota"


def _path(slug: str) -> Path:
    return settings.MEMORY_DIR / f"{slugify(slug)}.md"


def _parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else path.stem
    tags = next((l[5:].strip() for l in lines[1:4] if l.lower().startswith("tags:")), "")
    return {
        "slug": path.stem,
        "title": title,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "content": text,
        "links": sorted({slugify(l) for l in LINK_RE.findall(text)}),
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
    }


def all_notes() -> list:
    settings.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    notes = [_parse(p) for p in settings.MEMORY_DIR.glob("*.md")]
    return sorted(notes, key=lambda n: n["updated_at"], reverse=True)


def backlinks(slug: str) -> list:
    slug = slugify(slug)
    return [n["slug"] for n in all_notes() if slug in n["links"] and n["slug"] != slug]


def read_note(slug: str):
    path = _path(slug)
    if not path.exists():
        return None
    note = _parse(path)
    note["backlinks"] = backlinks(note["slug"])
    return note


def write_note(title: str, content: str, tags: str = "") -> dict:
    """Create or fully replace a note."""
    path = _path(title)
    header = f"# {title}\ntags: {tags}\n\n" if tags else f"# {title}\n\n"
    body = content if content.lstrip().startswith("# ") else header + content.strip() + "\n"
    path.write_text(body, encoding="utf-8")
    return _parse(path)


def load_profile(max_chars: int = 4000) -> str:
    path = _path(PROFILE_SLUG)
    return path.read_text(encoding="utf-8")[:max_chars] if path.exists() else ""


# ---- tools ---------------------------------------------------------------

async def memory_save(title: str, content: str, tags: str = "", mode: str = "append") -> dict:
    path = _path(title)
    if mode == "append" and path.exists():
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with path.open("a", encoding="utf-8") as f:
            f.write(f"\n## {stamp}\n{content.strip()}\n")
        note = _parse(path)
    else:
        note = write_note(title, content, tags)
    return {"saved": note["slug"], "links": note["links"]}


async def remember_fact(fact: str) -> dict:
    path = _path(PROFILE_SLUG)
    if not path.exists():
        path.write_text("# Perfil\ntags: perfil\n\nDatos estables sobre el usuario.\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"- {fact.strip()}\n")
    return {"saved": PROFILE_SLUG}


async def memory_search(query: str, limit: int = 5) -> dict:
    terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    scored = []
    for n in all_notes():
        hay_title, hay = n["title"].lower(), n["content"].lower()
        score = sum(hay.count(t) + 5 * (t in hay_title) + 3 * (t in n["tags"]) for t in terms)
        if score:
            idx = min((hay.find(t) for t in terms if t in hay), default=0)
            snippet = n["content"][max(0, idx - 150): idx + 350].strip()
            scored.append((score, {"slug": n["slug"], "title": n["title"], "snippet": snippet}))
    scored.sort(key=lambda x: -x[0])
    return {"results": [s for _, s in scored[:limit]]}


async def memory_read(title: str) -> dict:
    note = read_note(title)
    if not note:
        return {"error": f"No existe la nota '{title}'. Usa memory_search."}
    return {k: note[k] for k in ("slug", "title", "content", "links", "backlinks")}


async def memory_list() -> dict:
    return {"notes": [{"slug": n["slug"], "title": n["title"], "tags": n["tags"]} for n in all_notes()]}


TOOLS = [
    {
        "name": "memory_save",
        "description": "Guarda conocimiento a largo plazo en una nota markdown: procedimientos ('cómo hacer X'), "
                       "decisiones, contexto de proyectos. Enlaza notas relacionadas con [[Título]]. "
                       "Por defecto agrega al final si la nota existe.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título de la nota, p. ej. 'Reiniciar servidor de video'"},
                "content": {"type": "string", "description": "Markdown. Usa [[Otra nota]] para enlazar."},
                "tags": {"type": "string", "description": "Etiquetas separadas por coma"},
                "mode": {"type": "string", "enum": ["append", "replace"]},
            },
            "required": ["title", "content"],
        },
        "handler": memory_save,
    },
    {
        "name": "remember_fact",
        "description": "Guarda un dato corto y estable sobre el usuario (preferencias, gente, trabajo). "
                       "Estos datos se incluyen siempre en tu contexto.",
        "parameters": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]},
        "handler": remember_fact,
    },
    {
        "name": "memory_search",
        "description": "Busca en las notas guardadas. Úsalo antes de responder preguntas como "
                       "'¿cómo hacía X?' o '¿qué habíamos decidido de Y?'.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        "handler": memory_search,
    },
    {
        "name": "memory_read",
        "description": "Lee una nota completa con sus enlaces y backlinks.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
        "handler": memory_read,
    },
    {
        "name": "memory_list",
        "description": "Lista todas las notas guardadas.",
        "parameters": {"type": "object", "properties": {}},
        "handler": memory_list,
    },
]
