"""Discord as a remote channel: Talos DMs you briefings and alerts, and you can write or send
voice notes back from anywhere. Only the configured owner is ever answered.

Setup: create an application + bot at https://discord.com/developers/applications,
enable the "Message Content" intent, invite the bot to a server you share, then set
DISCORD_BOT_TOKEN and DISCORD_USER_ID in .env.
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
stt = None  # set by main.py
tts = None


def enabled() -> bool:
    return bool(settings.DISCORD_BOT_TOKEN and settings.DISCORD_USER_ID)


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
        _owner = await _client.fetch_user(int(settings.DISCORD_USER_ID))
    return _owner


async def send(title: str, body: str, audio_path: Optional[str] = None):
    """DM the owner. Silently does nothing when Discord isn't configured or connected."""
    if not _client or not _client.is_ready():
        return
    try:
        import discord
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
    global _client
    if not enabled():
        logger.info("Discord not configured (DISCORD_BOT_TOKEN / DISCORD_USER_ID)")
        return
    import discord

    intents = discord.Intents.default()
    intents.message_content = True
    intents.dm_messages = True
    client = discord.Client(intents=intents)
    owner_id = int(settings.DISCORD_USER_ID)
    channel_id = int(settings.DISCORD_CHANNEL_ID) if settings.DISCORD_CHANNEL_ID else None

    @client.event
    async def on_ready():
        logger.info(f"Discord connected as {client.user}")

    @client.event
    async def on_message(message):
        if message.author.bot or message.author.id != owner_id:
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
