"""The assistant loop: system prompt + memory + history -> LLM -> tools -> answer."""
import json
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app import tools
from app.core import db
from app.core.config import settings
from app.services.llm_service import llm
from app.tools import memory

logger = logging.getLogger(__name__)

MAX_STEPS = 6
HISTORY = 16

# Questions about live data must hit a tool; otherwise the model recycles stale numbers from history.
REALTIME = re.compile(
    r"\b(clima|tiempo hace|temperatura|llov|lluvia|weather|temperature|rain|noticia|news|headline|"
    r"lanzamiento|release|jira|ticket|pendiente|recu[eé]rdame|remind|recordatorio|reminder|"
    r"right now|ahora mismo|en este momento|today|hoy|orca|agentes|agents|d[oó]lar|dollar|trm)", re.I)


def _aged(message: dict) -> str:
    """Tag old turns with their age so the model knows their data is stale."""
    minutes = (datetime.now().astimezone() - datetime.fromisoformat(message["created_at"])).total_seconds() / 60
    if minutes < 10:
        return message["content"]
    age = f"{int(minutes)} min" if minutes < 120 else f"{minutes / 60:.0f} h"
    return f"[hace {age}; datos posiblemente desactualizados] {message['content']}"


def load_persona() -> str:
    """Personality and style from data/persona.md (kept out of git)."""
    path = settings.PERSONA_PATH
    return path.read_text(encoding="utf-8").strip()[:3000] if path.exists() else ""


def system_prompt(voice: bool, language: str = "es") -> str:
    now = datetime.now(ZoneInfo(settings.TIMEZONE))
    profile = memory.load_profile()
    who = f" de {settings.USER_NAME}" if settings.USER_NAME else ""
    parts = [
        f"Eres {settings.NAME}, el asistente personal{who}."
        + (" Tu nombre viene de Talos, el gigante de bronce que custodiaba Creta: vigilas, recuerdas y "
           "avisas a tiempo, sin dramatismo." if settings.NAME.lower() == "talos" else ""),
        f"Ahora es {now.strftime('%A %d de %B de %Y, %H:%M')} ({settings.TIMEZONE})."
        + (f" El usuario vive {settings.HOME}." if settings.HOME else ""),
        "REGLA CRÍTICA: no sabes nada en tiempo real. NUNCA inventes clima, temperaturas, noticias, "
        "lanzamientos, tickets, recordatorios ni notas: SIEMPRE llama primero la herramienta y responde "
        "solo con lo que devuelva. Si la herramienta falla, dilo. Los datos de mensajes anteriores ya "
        "están desactualizados: vuelve a llamar la herramienta cada vez.\n"
        "- clima/temperatura/lluvia → get_weather\n"
        "- titulares, lanzamientos de modelos de IA → get_news (category ia para modelos)\n"
        "- detalles de una noticia ('¿qué pasó con X?', 'cuéntame más') → search_articles: son los "
        "artículos completos que leíste para los boletines\n"
        "- dólar / tasa de cambio → get_dollar\n"
        "- agentes de código, Orca, '¿ya terminó…?' → orca_agents\n"
        "- 'en el proyecto X haz/revisa/mejora…' → orca_delegate (plan para analizar/proponer, edit solo si "
        "pide implementar); 'dile al agente que…' → orca_reply\n"
        "- Jira, tickets, qué me falta → jira_pending y list_reminders\n"
        "- 'recuérdame… a las X' → create_reminder; 'tengo que…/agrega a mis tareas' → add_task\n"
        "- 'guarda/anota/recuerda que…', o cuando te enseñe cómo se hace algo → memory_save "
        "(enlaza notas relacionadas con [[Título]]); datos personales estables → remember_fact\n"
        "- '¿cómo era/cómo hacía…?', '¿qué habíamos decidido…?' → memory_search antes de responder\n"
        "- investigar a fondo, comparar muchas fuentes → deep_research (avisa que tarda unos minutos)",
        "Para recordatorios calcula la fecha exacta a partir de la hora actual.",
    ]
    parts.append("ESTILO: información 100% concreta y comprimida: cifras, nombres, hechos; sin relleno, "
                 "sin repetir la pregunta, sin despedidas largas.")
    if settings.USER_TITLE:
        parts.append(f"Dirígete al usuario como '{settings.USER_TITLE}'.")
    persona = load_persona()
    if persona:
        parts.append(f"## Personalidad\n{persona}")
    if language == "en":
        parts.append("IDIOMA: responde SIEMPRE en inglés (English).")
    elif language == "auto":
        parts.append("IDIOMA: responde en el mismo idioma en que te escribe el usuario (español o inglés).")
    else:
        parts.append("IDIOMA: responde en español.")
    if voice:
        parts.append("Esta respuesta se va a leer en voz alta: sé breve (2-4 frases), sin markdown, "
                     "sin listas largas ni URLs.")
    if profile:
        parts.append(f"## Lo que sabes del usuario\n{profile}")
    return "\n\n".join(parts)


async def run(user_text: str, voice: bool = False) -> dict:
    language = db.language()
    """Process one user message. Returns {"text": ..., "tools": [...]}."""
    history = [{"role": m["role"], "content": _aged(m)}
               for m in db.recent_messages(HISTORY) if m["role"] in ("user", "assistant")]
    messages = [{"role": "system", "content": system_prompt(voice, language)}, *history,
                {"role": "user", "content": user_text}]
    db.add_message("user", user_text)

    used = []
    specs = tools.specs()
    answer = ""
    force_tool = bool(REALTIME.search(user_text))
    for step in range(MAX_STEPS):
        # step 0 decides whether to use tools: forced for live-data questions, otherwise let Qwen
        # reason briefly (thinking) so it doesn't answer from stale history
        think = step == 0 and not force_tool and "qwen" in llm.model.lower()
        turn = await llm.chat_with_tools(messages, specs, require_tool=force_tool and step == 0, think=think)
        if think and not turn["tool_calls"] and not turn["content"]:
            # reasoning got cut before the answer; ask again without thinking
            turn = await llm.chat_with_tools(messages, specs)
        if not turn["tool_calls"]:
            answer = turn["content"]
            break
        messages.append({
            "role": "assistant",
            "content": turn["content"],
            "tool_calls": [{"id": c["id"], "type": "function",
                            "function": {"name": c["name"], "arguments": json.dumps(c["arguments"], ensure_ascii=False)}}
                           for c in turn["tool_calls"]],
        })
        for call in turn["tool_calls"]:
            logger.info(f"Tool call: {call['name']}({call['arguments']})")
            result = await tools.call(call["name"], call["arguments"])
            used.append({"name": call["name"], "arguments": call["arguments"]})
            messages.append({"role": "tool", "tool_call_id": call["id"], "name": call["name"],
                             "content": result})
    else:
        answer = turn["content"] or "Me enredé usando herramientas; ¿me lo repites más concreto?"

    db.add_message("assistant", answer, {"tools": used} if used else None)
    return {"text": answer, "tools": used}

