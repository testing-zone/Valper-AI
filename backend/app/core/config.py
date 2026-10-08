"""Central configuration for Talos. Everything is read from environment (.env)."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
load_dotenv()  # also allow a .env in the current working directory


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _list(name: str, default: str) -> list:
    return [x.strip() for x in _env(name, default).split(",") if x.strip()]


class Settings:
    # Identity
    NAME = _env("ASSISTANT_NAME") or _env("VALPER_NAME", "Talos")
    USER_NAME = _env("ASSISTANT_USER_NAME") or _env("VALPER_USER_NAME", "")
    USER_TITLE = _env("USER_TITLE")  # how the assistant addresses you, e.g. "Sir"
    HOME = _env("HOME_DESCRIPTION")  # e.g. "en Medellín, Colombia"
    TIMEZONE = _env("TIMEZONE", "UTC")

    # Server
    HOST = _env("API_HOST", "127.0.0.1")
    PORT = int(_env("API_PORT", "8000"))

    # Storage
    DATA_DIR = Path(_env("DATA_DIR", str(ROOT_DIR / "data")))
    DB_PATH = DATA_DIR / "talos.db"
    PERSONA_PATH = DATA_DIR / "persona.md"  # your personality/style instructions (not in git)
    MEMORY_DIR = DATA_DIR / "memory"
    RESEARCH_DIR = DATA_DIR / "research"
    AUDIO_DIR = DATA_DIR / "audio"

    # LLM (TotalGPT, OpenAI-compatible)
    LLM_API_KEY = _env("TOTALGPT_API_KEY")
    LLM_BASE_URL = _env("TOTALGPT_BASE_URL", "https://api.totalgpt.ai/v1")
    LLM_MODEL = _env("TOTALGPT_MODEL", "Qwen-Qwen3.6-35B-A3B")
    # Cheaper/faster model for scheduled summaries; falls back to LLM_MODEL
    LLM_MODEL_FAST = _env("TOTALGPT_MODEL_FAST") or LLM_MODEL
    # auto: try native tool calling, fall back to prompt-based tool calls
    LLM_TOOL_MODE = _env("LLM_TOOL_MODE", "auto")
    LLM_TIMEOUT = float(_env("LLM_TIMEOUT", "90"))
    # Qwen3.x "thinking" adds latency and leaks reasoning into answers; off by default
    LLM_THINKING = _env("LLM_THINKING", "false").lower() == "true"

    # Speech
    WHISPER_MODEL = _env("WHISPER_MODEL", "turbo")  # large-v3-turbo
    STT_ENGINE = _env("STT_ENGINE")  # mlx (Apple Silicon GPU) | openai (CPU); empty = auto
    # infermatic = Kokoro hosted on TotalGPT (all voices, no local model); local = Kokoro on this machine
    TTS_PROVIDER = _env("TTS_PROVIDER", "infermatic")
    TTS_MODEL = _env("TTS_MODEL", "TTS-hexgrad-Kokoro-82M")
    TTS_LANG = _env("TTS_LANG", "e")  # local Kokoro only: 'e' = Spanish, 'a' = US English
    # Default voices per language (changeable from the UI). Blends: "bm_george(2)+bm_fable(1)"
    TTS_VOICE_ES = _env("TTS_VOICE_ES") or _env("TTS_VOICE", "em_alex(2)+em_santa(1)")
    TTS_VOICE_EN = _env("TTS_VOICE_EN", "bm_george(2)+bm_fable(1)")
    LANGUAGE = _env("LANGUAGE", "es")  # es | en (also switchable from the UI)

    # Places for weather and local news
    # "Name:lat:lon,Name:lat:lon"
    LOCATIONS = {
        name.strip(): (float(lat), float(lon))
        for name, lat, lon in (item.split(":") for item in _list("LOCATIONS", "London:51.5072:-0.1276"))
    }
    LOCATION_LABEL = _env("LOCATION_LABEL") or " · ".join(LOCATIONS)
    # Google News edition for national headlines, e.g. es-419:CO, en-US:US
    NEWS_EDITION = _env("NEWS_EDITION", "en-US:US")
    LOCAL_NEWS_QUERIES = _list("LOCAL_NEWS_QUERIES", ",".join(LOCATIONS))
    EXTRA_NEWS = _env("EXTRA_NEWS")  # "Label|query1,query2" e.g. "Inmobiliario|vivienda Colombia"
    CURRENCY = _env("CURRENCY", "")  # e.g. COP -> dollar rate in the briefing

    # Schedules (local time)
    DIGEST_HOURS = _env("DIGEST_HOURS", "6,9,12,15,18,21")
    LOCAL_NEWS_HOUR = int(_env("LOCAL_NEWS_HOUR", "12"))
    JIRA_HOUR = int(_env("JIRA_HOUR", "8"))

    # Jira (optional)
    JIRA_URL = _env("JIRA_URL").rstrip("/")
    JIRA_EMAIL = _env("JIRA_EMAIL")
    JIRA_API_TOKEN = _env("JIRA_API_TOKEN")
    JIRA_JQL = _env(
        "JIRA_JQL",
        "assignee = currentUser() AND statusCategory != Done ORDER BY duedate ASC, priority DESC",
    )

    # Deep research via Claude Code (headless)
    CLAUDE_BIN = _env("CLAUDE_BIN", "claude")
    CLAUDE_MODEL = _env("CLAUDE_MODEL")
    RESEARCH_TIMEOUT = int(_env("RESEARCH_TIMEOUT", "1800"))
    RESEARCH_TOOLS = _env("RESEARCH_TOOLS", "WebSearch,WebFetch,Read,Write")
    # Drop ANTHROPIC_API_KEY for the subprocess so Claude Code uses the claude.ai subscription
    CLAUDE_USE_SUBSCRIPTION = _env("CLAUDE_USE_SUBSCRIPTION", "true").lower() == "true"

    # Orca (Stably AI) coding-agent orchestrator; empty = auto-detect the CLI inside Orca.app
    ORCA_BIN = _env("ORCA_BIN")

    # Notifications
    NOTIFY_MACOS = _env("NOTIFY_MACOS", "true").lower() == "true"
    SPEAK_ON_MAC = _env("SPEAK_ON_MAC", "true").lower() == "true"

    # Discord (optional): DMs with briefings/alerts, and chat with the assistant from anywhere
    DISCORD_BOT_TOKEN = _env("DISCORD_BOT_TOKEN")
    DISCORD_USER_ID = _env("DISCORD_USER_ID")  # your user id; nobody else is answered
    DISCORD_CHANNEL_ID = _env("DISCORD_CHANNEL_ID")  # optional server channel to talk in
    DISCORD_AUDIO = _env("DISCORD_AUDIO", "true").lower() == "true"  # attach the spoken version

    @property
    def jira_enabled(self) -> bool:
        return bool(self.JIRA_URL and self.JIRA_EMAIL and self.JIRA_API_TOKEN)

    def ensure_dirs(self):
        for d in (self.DATA_DIR, self.MEMORY_DIR, self.RESEARCH_DIR, self.AUDIO_DIR):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
