"""Quiet mode: Talos keeps delivering things as text but stops talking out loud.

- Manual: quiet for N minutes, or until told otherwise.
- QUIET_HOURS in .env, e.g. "22-7".
- Optional AUTO_QUIET_ON_MIC: stay silent while any app is using the microphone (calls, meetings).
"""
import logging
import platform
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from app.core import db
from app.core.config import settings

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(ZoneInfo(settings.TIMEZONE))


def mic_in_use() -> bool:
    """True if the default input device is running in any process (CoreAudio, no permissions needed)."""
    if platform.system() != "Darwin":
        return False
    try:
        import ctypes
        import ctypes.util
        import struct

        ca = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreAudio"))

        class Addr(ctypes.Structure):
            _fields_ = [("sel", ctypes.c_uint32), ("scope", ctypes.c_uint32), ("elem", ctypes.c_uint32)]

        def prop(obj, selector):
            addr = Addr(struct.unpack(">I", selector.encode())[0], struct.unpack(">I", b"glob")[0], 0)
            val, size = ctypes.c_uint32(0), ctypes.c_uint32(4)
            ca.AudioObjectGetPropertyData(ctypes.c_uint32(obj), ctypes.byref(addr), 0, None,
                                          ctypes.byref(size), ctypes.byref(val))
            return val.value

        device = prop(1, "dIn ")  # default input device
        return bool(device and prop(device, "gone"))  # DeviceIsRunningSomewhere
    except Exception as e:
        logger.debug(f"mic check failed: {e}")
        return False


def _in_quiet_hours() -> bool:
    if not settings.QUIET_HOURS:
        return False
    start, _, end = settings.QUIET_HOURS.partition("-")
    h = _now().hour
    start, end = int(start), int(end)
    return start <= h < end if start < end else (h >= start or h < end)


def status() -> dict:
    until = db.get_prefs().get("quiet_until")
    manual = None
    if until == "forever":
        manual = "forever"
    elif until and datetime.fromisoformat(until) > _now():
        manual = until
    reason = ("manual" if manual else "quiet_hours" if _in_quiet_hours()
              else "microphone" if settings.AUTO_QUIET_ON_MIC and mic_in_use() else None)
    return {"quiet": bool(reason), "reason": reason, "until": manual, "quiet_hours": settings.QUIET_HOURS or None,
            "auto_mic": settings.AUTO_QUIET_ON_MIC}


def is_quiet() -> bool:
    return status()["quiet"]


def set_quiet(minutes: Optional[int]) -> dict:
    """minutes: N -> quiet for N minutes; 0 -> back to normal; None/-1 -> until told otherwise."""
    if minutes == 0:
        db.set_prefs({"quiet_until": None})
    elif minutes is None or minutes < 0:
        db.set_prefs({"quiet_until": "forever"})
    else:
        db.set_prefs({"quiet_until": (_now() + timedelta(minutes=minutes)).isoformat(timespec="minutes")})
    from app.core import events
    events.publish("quiet", status())
    return status()


async def quiet(minutes: int = 60) -> dict:
    from app.tools import notify
    await notify.stop_speaking()
    return set_quiet(minutes)


async def unquiet() -> dict:
    return set_quiet(0)


async def stop_speaking() -> dict:
    from app.tools import notify
    await notify.stop_speaking()
    return {"stopped": True}


TOOLS = [
    {
        "name": "quiet",
        "description": "Silencia la voz de Talos (sigue enviando todo por texto). minutes=60 por defecto; "
                       "-1 = hasta nuevo aviso. Úsalo para 'cállate', 'estoy en una reunión', 'quiet for an hour'.",
        "parameters": {"type": "object", "properties": {"minutes": {"type": "integer"}}},
        "handler": quiet,
    },
    {
        "name": "unquiet",
        "description": "Vuelve a hablar en voz alta.",
        "parameters": {"type": "object", "properties": {}},
        "handler": unquiet,
    },
    {
        "name": "stop_speaking",
        "description": "Detiene lo que Talos esté diciendo en este momento.",
        "parameters": {"type": "object", "properties": {}},
        "handler": stop_speaking,
    },
]
