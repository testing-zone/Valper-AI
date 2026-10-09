"""Tool registry. To add an integration (GPU servers, ComfyUI, Orca...), create a module
with a TOOLS list and add it here."""
import json
import logging

from app.tools import articles, finance, jira, memory, news, orca, reminders, research, tasks, weather

logger = logging.getLogger(__name__)

_MODULES = [weather, finance, news, articles, memory, tasks, reminders, research, jira, orca]
REGISTRY = {t["name"]: t for m in _MODULES for t in m.TOOLS}


def specs() -> list:
    """Tool definitions without handlers, for the LLM."""
    return [{k: v for k, v in t.items() if k != "handler"} for t in REGISTRY.values()]


async def call(name: str, arguments: dict) -> str:
    tool = REGISTRY.get(name)
    if not tool:
        return json.dumps({"error": f"Herramienta desconocida: {name}"})
    try:
        result = await tool["handler"](**(arguments or {}))
    except TypeError as e:
        result = {"error": f"Argumentos inválidos: {e}"}
    except Exception as e:
        logger.exception(f"Tool {name} failed")
        result = {"error": str(e)}
    text = json.dumps(result, ensure_ascii=False, default=str)
    return text[:8000]
