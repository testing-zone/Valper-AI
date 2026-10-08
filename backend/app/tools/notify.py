"""Push something to the user: feed entry + live UI event + macOS notification."""
import asyncio
import logging
import platform

from app.core import db, events
from app.core.config import settings

logger = logging.getLogger(__name__)

tts = None  # set by main.py

# ffmpeg versions of the browser effects, so the Mac can speak with no browser open
FFMPEG_FX = {
    "radio": "highpass=f=450,lowpass=f=3200,acompressor=threshold=-18dB:ratio=6,volume=1.6,"
             "asoftclip=type=tanh,aecho=0.6:0.3:12:0.2",
    "colossus": "asetrate=24000*0.94,aresample=24000,aecho=0.8:0.6:11:0.45,highpass=f=120",
    "sala": "bass=g=4,aecho=0.8:0.7:60|120:0.3|0.2",
}

_speak_lock = asyncio.Lock()


async def speak_on_mac(text: str):
    """Synthesize with the user's voice prefs and play it through the Mac speakers."""
    if not settings.SPEAK_ON_MAC or platform.system() != "Darwin" or not tts or not tts.is_ready:
        return
    from app.core import db as _db
    path = await tts.synthesize(text)
    if not path:
        return
    effect = _db.get_prefs().get("effect", "none")
    async with _speak_lock:  # never talk over itself
        try:
            if effect in FFMPEG_FX:
                out = path.rsplit(".", 1)[0] + f".{effect}.wav"
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", FFMPEG_FX[effect], out)
                await proc.wait()
                if proc.returncode == 0:
                    path = out
            proc = await asyncio.create_subprocess_exec("afplay", path)
            await proc.wait()
        except Exception as e:
            logger.warning(f"Speaking on Mac failed: {e}")


async def macos_notification(title: str, message: str):
    if not settings.NOTIFY_MACOS or platform.system() != "Darwin":
        return
    esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')[:240]
    script = f'display notification "{esc(message)}" with title "{esc(title)}" sound name "Glass"'
    try:
        proc = await asyncio.create_subprocess_exec("osascript", "-e", script)
        await proc.wait()
    except Exception as e:
        logger.warning(f"macOS notification failed: {e}")


async def push(kind: str, title: str, body: str, data: dict = None, speak: str = None) -> dict:
    """speak: text to say out loud (on the Mac if SPEAK_ON_MAC, otherwise in the open browser tab)."""
    item = db.add_feed(kind, title, body, data)
    events.publish("feed", {**item, "speak": bool(speak) and not settings.SPEAK_ON_MAC, "speech": speak})
    await macos_notification(f"{settings.NAME} · {title}", body.replace("*", "").split("\n")[0])
    if speak and settings.SPEAK_ON_MAC:
        asyncio.create_task(speak_on_mac(speak))
    return item
