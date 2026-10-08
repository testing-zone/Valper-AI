"""Scheduled briefings: periodic digest, local news at noon, Jira pending work."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core import db
from app.core.config import settings
from app.services.llm_service import LLMError, llm
from app.agent import load_persona
from app.tools import articles, finance, jira, news, notify, weather

logger = logging.getLogger(__name__)

STYLE = (
    "Escribe en español, en markdown. Información 100% concreta y comprimida: cifras, nombres, hechos; "
    "cero relleno, cero adjetivos vacíos, una línea por ítem. Cita cada noticia con [titular](url). "
    "Descarta lo irrelevante. No inventes nada que no esté en los datos."
)


async def _spoken(body: str) -> str:
    """Compressed version to read aloud: what matters, no links, in the user's language."""
    en = db.language() == "en"
    title = f" Address the user as {settings.USER_TITLE}." if settings.USER_TITLE else ""
    try:
        return await llm.complete([
            {"role": "system", "content":
                f"You are {settings.NAME}, a personal assistant.{title} {load_persona()}\n"
                + ("Speak in English. " if en else "Habla en español. ")
                + "Turn this briefing into a spoken summary of max 7 short sentences: the substance of the "
                  "news (what happened, numbers, names), most important first. No markdown, no URLs."},
            {"role": "user", "content": body},
        ], model=settings.LLM_MODEL_FAST, max_tokens=350, temperature=0.5)
    except LLMError:
        return ""


async def _summarize(instruction: str, raw: str, fallback: str) -> str:
    if not llm.is_available:
        return fallback
    lang = " Write the whole briefing in ENGLISH (translate headlines)." if db.language() == "en" else ""
    try:
        return await llm.complete([
            {"role": "system", "content": f"Eres {settings.NAME}, asistente personal. {STYLE}{lang}"},
            {"role": "user", "content": f"{instruction}\n\nDATOS:\n{raw}"},
        ], model=settings.LLM_MODEL_FAST, max_tokens=1200, temperature=0.3)
    except LLMError as e:
        logger.warning(f"Summary failed, using raw fallback: {e}")
        return fallback


def _now():
    return datetime.now(ZoneInfo(settings.TIMEZONE))


async def digest() -> dict:
    """Every few hours: weather, currency, local news, AI releases, extra sections, headlines.
    The articles are actually read, so the summary is about their content and follow-up
    questions can be answered from them (search_articles)."""
    raw, fallback = [], []

    try:
        w = weather.format_weather(await weather.get_weather())
        raw.append(f"CLIMA (ahora, hoy y mañana):\n{w}")
        fallback.append(f"### Clima\n{w}")
    except Exception as e:
        logger.warning(f"Weather failed: {e}")
    if settings.CURRENCY:
        try:
            d = finance.format_dollar(await finance.get_dollar())
            raw.append(f"DÓLAR:\n{d}")
            fallback.append(f"### Dólar\n{d}")
        except Exception as e:
            logger.warning(f"Dollar failed: {e}")

    # (category, label, headlines to consider, articles to read)
    sections = [("local", settings.LOCATION_LABEL.upper(), 10, 4),
                ("ia", "IA: MODELOS NUEVOS, HUGGING FACE, OPENAI, ETC.", 6, 4)]
    sections += [(label, label.upper(), 6, 3) for label in news.EXTRA]
    sections += [("nacional", "TITULARES NACIONALES", 6, 3), ("mundo", "TITULARES MUNDO", 4, 2)]
    counts = {}
    for cat, label, n, to_read in sections:
        items = await news.fresh_items(cat, limit_per_feed=n)
        counts[cat] = len(items)
        if not items:
            continue
        read = await articles.read_articles(items, cat, to_read)
        rest = items[to_read:15]
        block = articles.digest_block(read)
        if rest:
            block += "\nOTROS TITULARES:\n" + news.format_items(rest)
        raw.append(f"== {label} ==\n{block}")
        fallback.append(f"### {label.title()}\n" + news.format_items(items[:6]))
    articles.prune()

    pending = db.query("SELECT text, due_at FROM reminders WHERE done = 0 ORDER BY due_at LIMIT 5")
    if pending:
        raw.append("PENDIENTES:\n" + "\n".join(f"- {r['text']} ({r['due_at'][:16]})" for r in pending))

    body = await _summarize(
        "Boletín en este orden, solo secciones con datos: **Clima** (por ciudad: ahora, resto del día y mañana, "
        "una línea), **Dólar**, luego una sección por cada bloque de noticias (local, IA, extras, nacional, mundo). "
        "Para las noticias que tienen texto del artículo, resume en 1-2 líneas QUÉ dice (hechos, cifras, "
        "nombres), no solo el titular. IA: modelo, empresa y qué trae. Máx 4 ítems por sección, cada uno con "
        "[fuente](url). Cierra con **Pendientes** si hay.",
        "\n\n".join(raw), "\n\n".join(fallback) or "Sin novedades.")
    speech = await _spoken(body)
    title = f"Boletín {_now().strftime('%H:%M')}"
    return await notify.push("digest", title, body, counts, speak=speech or None)


async def local_news() -> dict:
    """Noon briefing: important local news."""
    items = await news.fresh_items("local", limit_per_feed=15)
    if not items:
        return await notify.push("local", f"Noticias {settings.LOCATION_LABEL}", "No encontré noticias nuevas hoy.")
    body = await _summarize(
        f"Resume las noticias más importantes de hoy en {settings.LOCATION_LABEL} (orden público, movilidad, servicios, "
        "clima, economía local, eventos). Agrupa por ciudad, máximo 8 en total, 1-2 líneas cada una.",
        news.format_items(items), news.format_items(items[:10]))
    speech = await _spoken(body)
    return await notify.push("local", f"Noticias {settings.LOCATION_LABEL}", body, {"count": len(items)},
                             speak=speech or None)


async def jira_briefing() -> dict:
    if not settings.jira_enabled:
        return {"skipped": "jira not configured"}
    data = await jira.jira_pending()
    issues = data.get("issues", [])
    if not issues:
        return await notify.push("jira", "Jira", "No tienes tickets pendientes. 🎉")
    raw = "\n".join(f"- [{i['key']}]({i['url']}) {i['summary']} | {i['status']} | prioridad {i['priority']} "
                    f"| vence {i['due'] or 'sin fecha'}" for i in issues)
    body = await _summarize(
        f"Hoy es {_now().strftime('%Y-%m-%d')}. Dime qué tengo pendiente en Jira: primero lo vencido o que vence "
        "pronto, luego lo de mayor prioridad. Sé directo, tipo 'oye, te está faltando esto'.", raw, raw)
    return await notify.push("jira", "Pendientes en Jira", body, {"count": len(issues)})


async def fire_reminders():
    from app.tools.reminders import due_reminders
    for r in due_reminders():
        who = f"{settings.USER_TITLE}, " if settings.USER_TITLE else ""
        intro = f"{who}a reminder: " if db.language() == "en" else f"{who}le recuerdo: "
        await notify.push("reminder", "Recordatorio", r["text"], {"reminder_id": r["id"]}, speak=intro + r["text"])


JOBS = {
    "digest": digest,
    "local": local_news,
    "jira": jira_briefing,
}
