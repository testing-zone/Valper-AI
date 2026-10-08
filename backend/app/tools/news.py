"""News and AI model releases from RSS feeds and the Hugging Face API."""
import asyncio
import logging
from urllib.parse import quote

import feedparser
import httpx

from app.core import db
from app.core.config import settings

logger = logging.getLogger(__name__)


def _edition(spec: str):
    """'es-419:CO' -> ('es-419', 'CO')"""
    hl, gl = (spec.split(":") + ["US"])[:2]
    return hl, gl


def google_news(query: str = "", edition: str = None) -> str:
    hl, gl = _edition(edition or settings.NEWS_EDITION)
    lang = hl.split("-")[0]
    params = f"hl={hl}&gl={gl}&ceid={gl}:{lang}"
    if not query:
        return f"https://news.google.com/rss?{params}"
    return f"https://news.google.com/rss/search?q={quote(query)}&{params}"


def _extra_sections() -> dict:
    """EXTRA_NEWS="Inmobiliario|vivienda Colombia,sector inmobiliario;Cripto|bitcoin" -> {label: [queries]}"""
    out = {}
    for block in filter(None, (b.strip() for b in settings.EXTRA_NEWS.split(";"))):
        label, _, queries = block.partition("|")
        out[label.strip()] = [q.strip() for q in queries.split(",") if q.strip()]
    return out


EXTRA = _extra_sections()

FEEDS = {
    "nacional": [google_news()],
    "mundo": [google_news(edition="en-US:US")],
    "ia": [
        "https://huggingface.co/blog/feed.xml",
        "https://openai.com/news/rss.xml",
        "https://deepmind.google/blog/rss.xml",
        google_news("Anthropic Claude when:2d", "en-US:US"),
        google_news("new AI model release when:1d", "en-US:US"),
        google_news("open source LLM released when:2d", "en-US:US"),
    ],
    "local": [google_news(f"{q} when:1d") for q in settings.LOCAL_NEWS_QUERIES],
    **{label: [google_news(f"{q} when:2d") for q in queries] for label, queries in EXTRA.items()},
}

UA = {"User-Agent": "Mozilla/5.0 (personal assistant)"}


async def _fetch_feed(client: httpx.AsyncClient, url: str, limit: int) -> list:
    try:
        r = await client.get(url, headers=UA, follow_redirects=True)
        r.raise_for_status()
        parsed = feedparser.parse(r.content)
        items = []
        for e in parsed.entries[:limit]:
            source = getattr(getattr(e, "source", None), "title", None) or parsed.feed.get("title", "")
            title = e.get("title", "").strip()
            if source and title.endswith(f" - {source}"):
                title = title[: -len(source) - 3]
            items.append({
                "title": title,
                "link": e.get("link", ""),
                "source": source,
                "published": e.get("published", ""),
            })
        return items
    except Exception as ex:
        logger.warning(f"Feed failed {url}: {ex}")
        return []


async def fetch_category(category: str, limit_per_feed: int = 8) -> list:
    urls = FEEDS.get(category, [])
    async with httpx.AsyncClient(timeout=20) as client:
        results = await asyncio.gather(*[_fetch_feed(client, u, limit_per_feed) for u in urls])
    seen, items = set(), []
    for item in (i for batch in results for i in batch):
        key = item["title"].lower()[:80]
        if item["link"] and key not in seen:
            seen.add(key)
            items.append(item)
    return items


async def trending_models(limit: int = 10) -> list:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get("https://huggingface.co/api/models",
                             params={"sort": "trendingScore", "limit": limit}, headers=UA)
        r.raise_for_status()
        return [{
            "title": m["id"],
            "link": f"https://huggingface.co/{m['id']}",
            "source": "Hugging Face trending",
            "likes": m.get("likes"),
            "task": m.get("pipeline_tag"),
        } for m in r.json()]


async def fresh_items(category: str, limit_per_feed: int = 8) -> list:
    """Items in a category that were not included in any previous briefing."""
    items = await fetch_category(category, limit_per_feed)
    if category == "ia":
        try:
            items += await trending_models()
        except Exception as ex:
            logger.warning(f"HF trending failed: {ex}")
    unseen = db.filter_unseen([i["link"] for i in items])
    return [i for i in items if i["link"] in unseen]


async def get_news(category: str = "nacional", query: str = "") -> dict:
    if query:
        async with httpx.AsyncClient(timeout=20) as client:
            items = await _fetch_feed(client, google_news(query), 10)
    else:
        items = await fetch_category(category)
        if category == "ia":
            items += await trending_models(5)
    return {"items": items[:20]}


def format_items(items: list) -> str:
    return "\n".join(f"- [{i['title']}]({i['link']}) — {i.get('source', '')}" for i in items)


TOOLS = [
    {
        "name": "get_news",
        "description": "Titulares recientes. Categorías: nacional, mundo, ia (lanzamientos de modelos), "
                       f"local ({settings.LOCATION_LABEL}){''.join(', ' + k for k in EXTRA)}. "
                       "O una búsqueda libre con `query`.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": list(FEEDS.keys())},
                "query": {"type": "string", "description": "Búsqueda libre en Google News (opcional)"},
            },
        },
        "handler": get_news,
    }
]
