"""Discord as a remote channel: Talos DMs you briefings and alerts, and you can write or send
voice notes back from anywhere. Only the configured owner is ever answered.

Setup: create an application + bot at https://discord.com/developers/applications,
enable the "Message Content" intent and put DISCORD_BOT_TOKEN in .env. On start Talos
posts the invite link and a 6-digit pairing code (feed + macOS notification); send the
code to the bot and you become its owner. DISCORD_USER_ID can also be set by hand.
"""
import asyncio
import logging
import os
import tempfile
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_LEN = 1900  # Discord limit is 2000 per message

_client = None
_owner = None
_pair_code = None
stt = None  # set by main.py
tts = None


def owner_id() -> Optional[int]:
    from app.core import db
    value = settings.DISCORD_USER_ID or db.get_prefs().get("discord_owner")
    return int(value) if value else None


def enabled() -> bool:
    return bool(settings.DISCORD_BOT_TOKEN and owner_id())


def invite_url() -> str:
    """The application id is the base64 first segment of the bot token."""
    import base64
    first = settings.DISCORD_BOT_TOKEN.split(".")[0]
    app_id = base64.b64decode(first + "=" * (-len(first) % 4)).decode()
    # Send Messages + Attach Files + Read Message History + View Channels
    return f"https://discord.com/oauth2/authorize?client_id={app_id}&scope=bot&permissions=101376"


def _chunks(text: str):
    """Split on paragraph/line boundaries under Discord's message limit."""
    buf = ""
    for line in text.split("\n"):
        while len(line) > MAX_LEN:
            if buf:
                yield buf
                buf = ""
            yield line[:MAX_LEN]
            line = line[MAX_LEN:]
        if len(buf) + len(line) + 1 > MAX_LEN:
            yield buf
            buf = ""
        buf += line + "\n"
    if buf.strip():
        yield buf


async def _owner_dm():
    global _owner
    if _owner is None and _client:
        _owner = await _client.fetch_user(owner_id())
    return _owner


async def send(title: str, body: str, audio_path: Optional[str] = None):
    """DM the owner. Silently does nothing when Discord isn't configured or connected."""
    if not _client or not _client.is_ready():
        return
    try:
        import discord
        if not owner_id():
            return
        user = await _owner_dm()
        text = f"**{title}**\n{body}" if title else body
        # wrap links in <> so Discord doesn't add a big preview for every news link
        import re
        text = re.sub(r"\]\((https?://[^)]+)\)", r"](<\1>)", text)
        parts = list(_chunks(text))
        for i, part in enumerate(parts):
            last = i == len(parts) - 1
            if last and audio_path and os.path.exists(audio_path):
                await user.send(part, file=discord.File(audio_path, filename="talos.mp3"))
            else:
                await user.send(part)
    except Exception as e:
        logger.warning(f"Discord send failed: {e}")


async def _reply_audio(text: str) -> Optional[str]:
    """Spoken reply with the user's voice and effect, as a file for Discord."""
    from app.tools.notify import render_speech
    try:
        return await render_speech(text)
    except Exception as e:
        logger.info(f"No audio reply: {e}")
        return None


async def _handle(message):
    from app import agent
    text = message.content.strip()
    voice_in = False
    audio = next((a for a in message.attachments
                  if (a.content_type or "").startswith("audio") or a.filename.endswith((".ogg", ".mp3", ".m4a", ".wav"))),
                 None)
    if audio and stt and stt.is_ready:
        suffix = os.path.splitext(audio.filename)[1] or ".ogg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            await audio.save(tmp.name)
        try:
            heard = await stt.transcribe(tmp.name)
        finally:
            os.unlink(tmp.name)
        if heard:
            voice_in = True
            text = f"{text}\n{heard}".strip()
            await message.channel.send(f"> 🎙 {heard}")
    if not text:
        return
    async with message.channel.typing():
        try:
            result = await agent.run(text, voice=voice_in)
            answer = result["text"] or "…"
        except Exception as e:
            logger.exception("Discord turn failed")
            answer = f"⚠ {e}"
    audio_path = await _reply_audio(answer) if voice_in else None
    for i, part in enumerate(_chunks(answer)):
        if audio_path and i == 0:
            import discord
            await message.channel.send(part, file=discord.File(audio_path, filename="talos.mp3"))
        else:
            await message.channel.send(part)


async def start():
    global _client, _pair_code
    if not settings.DISCORD_BOT_TOKEN:
        logger.info("Discord not configured (DISCORD_BOT_TOKEN)")
        return
    import random
    import discord
    from app.core import db
    from app.tools import notify

    intents = discord.Intents.default()
    intents.message_content = True
    intents.dm_messages = True
    client = discord.Client(intents=intents)
    channel_id = int(settings.DISCORD_CHANNEL_ID) if settings.DISCORD_CHANNEL_ID else None

    @client.event
    async def on_ready():
        global _pair_code
        logger.info(f"Discord connected as {client.user}")
        if not owner_id():
            _pair_code = f"{random.randint(0, 999999):06d}"
            await notify.push(
                "discord", "Conectar Discord",
                f"1. Invita el bot a un servidor tuyo: {invite_url()}\n"
                f"2. Mándale este código por mensaje directo (o mencionándolo): **{_pair_code}**")

    @client.event
    async def on_message(message):
        global _pair_code, _owner
        if message.author.bot:
            return
        if not owner_id():
            if _pair_code and _pair_code in message.content:
                db.set_prefs({"discord_owner": str(message.author.id)})
                _pair_code, _owner = None, None
                await message.channel.send(f"Emparejado. A partir de ahora solo te respondo a ti, {message.author.name}.")
            return
        if message.author.id != owner_id():
            return
        is_dm = message.guild is None
        in_channel = channel_id and message.channel.id == channel_id
        mentioned = client.user in message.mentions
        if is_dm or in_channel or mentioned:
            await _handle(message)

    _client = client
    asyncio.create_task(client.start(settings.DISCORD_BOT_TOKEN))


async def stop():
    if _client:
        await _client.close()
