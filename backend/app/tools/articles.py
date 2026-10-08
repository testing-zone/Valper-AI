"""Reads the actual articles behind the headlines and keeps them for follow-up questions.

Google News links are decoded to the publisher URL, the page is fetched and the main
text extracted (trafilatura). Articles live in SQLite for a few days so the assistant
can answer "tell me more about X" with what the article actually says.
"""
import asyncio
import logging
import re
from typing import Optional

import httpx

from app.core import db

logger = logging.getLogger(__name__)

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
BOILERPLATE = re.compile(r"cookie|suscr[ií]b|newsletter|inicia sesi[oó]n|derechos reservados|"
                         r"all rights reserved|sign up|subscribe", re.I)
KEEP_DAYS = 4



def _decode(link: str) -> str:
    if "news.google.com" not in link:
        return link
    try:
        from googlenewsdecoder import gnewsdecoder
        result = gnewsdecoder(link, interval=0)
        return result.get("decoded_url") or link if result.get("status") or result.get("success") else link
    except Exception as e:
        logger.debug(f"decode failed: {e}")
        return link


def _extract(html: str) -> str:
    import trafilatura
    text = trafilatura.extract(html, favor_precision=True, include_comments=False) or ""
    paragraphs = [p for p in text.split("\n") if p.strip() and not BOILERPLATE.search(p[:200])]
    return "\n".join(paragraphs)


async def _read_one(client: httpx.AsyncClient, item: dict, category: str) -> Optional[dict]:
    url = await asyncio.to_thread(_decode, item["link"])
    cached = db.query_one("SELECT * FROM articles WHERE url = ?", (url,))
    if cached:
        return cached
    try:
        r = await client.get(url, headers=UA, follow_redirects=True)
        r.raise_for_status()
        text = await asyncio.to_thread(_extract, r.text)
    except Exception as e:
        logger.info(f"Could not read {url}: {e}")
        text = ""
    db.execute("INSERT OR REPLACE INTO articles (url, title, source, category, text, fetched_at) "
               "VALUES (?, ?, ?, ?, ?, ?)", (url, item["title"], item.get("source"), category, text, db.now_iso()))
    return db.query_one("SELECT * FROM articles WHERE url = ?", (url,))


async def read_articles(items: list, category: str, limit: int) -> list:
    """Fetch and store the first `limit` articles of a list of feed items."""
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient(timeout=15) as client:
        async def guarded(item):
            async with sem:
                return await _read_one(client, item, category)
        results = await asyncio.gather(*[guarded(i) for i in items[:limit]])
    return [a for a in results if a]


def digest_block(articles: list, chars: int = 900) -> str:
    """Article excerpts for the summarizer prompt."""
    out = []
    for a in articles:
        body = (a["text"] or "").strip()[:chars] or "(no se pudo leer el texto; usa solo el titular)"
        out.append(f"### {a['title']} — {a['source'] or ''}\nURL: {a['url']}\n{body}")
    return "\n\n".join(out)


def prune():
    db.execute(f"DELETE FROM articles WHERE fetched_at < datetime('now', '-{KEEP_DAYS} days')")


# ---- tools -----------------------------------------------------------------

async def search_articles(query: str, limit: int = 4) -> dict:
    terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    if not terms:
        return {"results": []}
    scored = []
    for a in db.query("SELECT * FROM articles ORDER BY fetched_at DESC LIMIT 400"):
        title, text = a["title"].lower(), (a["text"] or "").lower()
        score = sum(4 * (t in title) + min(text.count(t), 5) for t in terms)
        if score:
            scored.append((score, a))
    scored.sort(key=lambda x: -x[0])
    return {"results": [{"title": a["title"], "source": a["source"], "url": a["url"],
                         "date": a["fetched_at"][:16], "text": (a["text"] or "")[:2500]}
                        for _, a in scored[:limit]]}


async def read_article(url: str) -> dict:
    a = db.query_one("SELECT * FROM articles WHERE url = ?", (url,))
    if not a:
        a = await _read_one(httpx.AsyncClient(timeout=15), {"link": url, "title": url}, "manual")
    return {"title": a["title"], "url": a["url"], "text": (a["text"] or "")[:8000]}


TOOLS = [
    {
        "name": "search_articles",
        "description": "Busca en los artículos completos que ya leíste para los boletines (últimos días). "
                       "Úsalo cuando pregunten detalles de una noticia: '¿qué pasó con X?', 'cuéntame más de Y'.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        "handler": search_articles,
    },
    {
        "name": "read_article",
        "description": "Lee el texto completo de un artículo por su URL.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
        "handler": read_article,
    },
]
