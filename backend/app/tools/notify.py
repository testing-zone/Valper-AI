"""Push something to the user: feed entry + live UI event + macOS notification."""
import asyncio
import logging
import os
import platform
from typing import Optional

from app.core import db, events
from app.core.config import settings

logger = logging.getLogger(__name__)

tts = None  # set by main.py

# ffmpeg versions of the browser effects, so the Mac can speak with no browser open.
# Every chain ends in loudness normalization: the band-pass filters lose a lot of energy
# (the radio voice measured -44 LUFS, ~8x quieter than the raw voice).
LOUDNORM = "loudnorm=I=-15:TP=-1.5:LRA=11"
FFMPEG_FX = {
    "none": LOUDNORM,
    "radio": "highpass=f=450,lowpass=f=3200,acompressor=threshold=-18dB:ratio=6,"
             "asoftclip=type=tanh,aecho=0.6:0.3:12:0.2," + LOUDNORM,
    "colossus": "asetrate=24000*0.94,aresample=24000,aecho=0.8:0.6:11:0.45,highpass=f=120," + LOUDNORM,
    "sala": "bass=g=4,aecho=0.8:0.7:60|120:0.3|0.2," + LOUDNORM,
}

_speak_lock = asyncio.Lock()
_player = None  # current afplay process, so it can be stopped


async def stop_speaking():
    """Stop whatever is being said right now (Mac speakers and any open browser tab)."""
    global _player
    if _player and _player.returncode is None:
        _player.terminate()
    _player = None
    events.publish("stop_audio", {})


async def render_speech(text: str) -> Optional[str]:
    """Synthesize with the user's voice prefs and apply their effect. Returns an mp3 path."""
    if not tts or not tts.is_ready:
        return None
    path = await tts.synthesize(text)
    if not path:
        return None
    effect = db.get_prefs().get("effect", "none")
    effect = effect if effect in FFMPEG_FX else "none"
    if effect:
        out = path.rsplit(".", 1)[0] + f".{effect}.mp3"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", FFMPEG_FX[effect], "-ar", "24000",
            "-b:a", "96k", out)
        await proc.wait()
        if proc.returncode == 0:
            return out
    return path


async def speak_on_mac(text: str = None, path: str = None):
    """Play speech through the Mac speakers (one at a time)."""
    global _player
    from app.tools import quiet
    if not settings.SPEAK_ON_MAC or platform.system() != "Darwin" or quiet.is_quiet():
        return
    path = path or await render_speech(text)
    if not path:
        return
    async with _speak_lock:  # never talk over itself
        try:
            if quiet.is_quiet():  # muted while waiting for the previous message
                return
            # talos-player registers as macOS "Now Playing": the keyboard ⏯ key pauses/resumes
            # Talos like music and ⏭ skips. While paused, later messages wait their turn.
            player = settings.ROOT_PLAYER if os.path.exists(settings.ROOT_PLAYER) else None
            cmd = [player, path, "Talos"] if player else ["afplay", path]
            _player = await asyncio.create_subprocess_exec(*cmd)
            await _player.wait()
        except Exception as e:
            logger.warning(f"Speaking on Mac failed: {e}")


async def macos_notification(title: str, message: str):
    if not settings.NOTIFY_MACOS or platform.system() != "Darwin":
        return
    esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')[:240]
    from app.tools import quiet
    sound = "" if quiet.is_quiet() else ' sound name "Glass"'
    script = f'display notification "{esc(message)}" with title "{esc(title)}"{sound}'
    try:
        proc = await asyncio.create_subprocess_exec("osascript", "-e", script)
        await proc.wait()
    except Exception as e:
        logger.warning(f"macOS notification failed: {e}")


async def push(kind: str, title: str, body: str, data: dict = None, speak: str = None) -> dict:
    """Deliver something to the user: feed + live UI event + macOS notification + Discord DM,
    and say `speak` out loud (Mac speakers, and as an audio attachment on Discord)."""
    item = db.add_feed(kind, title, body, data)
    from app.tools import quiet
    events.publish("feed", {**item, "speak": bool(speak) and not settings.SPEAK_ON_MAC and not quiet.is_quiet(),
                            "speech": speak})
    await macos_notification(f"{settings.NAME} · {title}", body.replace("*", "").split("\n")[0])
    asyncio.create_task(_deliver(title, body, speak))
    return item


async def _deliver(title: str, body: str, speak: Optional[str]):
    from app.integrations import discord_bot
    audio = await render_speech(speak) if speak else None
    if discord_bot.enabled():
        await discord_bot.send(title, body, audio if settings.DISCORD_AUDIO else None)
    if audio:
        await speak_on_mac(path=audio)
