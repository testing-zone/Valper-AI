"""Speech-to-text with Whisper large-v3-turbo.

Engine `mlx` runs on the Apple Silicon GPU (~1 s per phrase); `openai` is the
reference implementation on CPU (slower, works anywhere).
"""
import asyncio
import logging
import os
import platform
import tempfile
import time
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

MLX_MODELS = {
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "large": "mlx-community/whisper-large-v3-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "base": "mlx-community/whisper-base-mlx",
}


def _default_engine() -> str:
    return "mlx" if platform.system() == "Darwin" and platform.machine() == "arm64" else "openai"


class STTService:
    def __init__(self):
        self.engine = settings.STT_ENGINE or _default_engine()
        self.model_name = settings.WHISPER_MODEL
        self.model = None
        self.is_ready = False
        self.last_latency_ms: Optional[int] = None
        self.last_language: Optional[str] = None

    async def initialize(self):
        try:
            if self.engine == "mlx":
                import mlx_whisper  # noqa: F401
                self.model = MLX_MODELS.get(self.model_name, self.model_name)
                # warm-up downloads and loads the weights once
                await asyncio.to_thread(self._warmup_mlx)
            else:
                import whisper
                self.model = await asyncio.to_thread(whisper.load_model, self.model_name)
            self.is_ready = True
            logger.info(f"Whisper {self.model_name} ready ({self.engine})")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper ({self.engine}): {e}")
            raise

    def _warmup_mlx(self):
        import mlx_whisper
        import numpy as np
        mlx_whisper.transcribe(np.zeros(16000, dtype=np.float32), path_or_hf_repo=self.model)

    def _transcribe_sync(self, path: str, language: Optional[str]) -> dict:
        if self.engine == "mlx":
            import mlx_whisper
            return mlx_whisper.transcribe(path, path_or_hf_repo=self.model, language=language)
        return self.model.transcribe(path, language=language, fp16=False)

    async def transcribe(self, file_path: str, language: Optional[str] = None) -> str:
        """Transcribe an audio file. language=None auto-detects (Spanish/English mixed)."""
        if not self.is_ready:
            return ""
        try:
            start = time.monotonic()
            result = await asyncio.to_thread(self._transcribe_sync, file_path, language)
            self.last_latency_ms = int((time.monotonic() - start) * 1000)
            self.last_language = result.get("language")
            return (result.get("text") or "").strip()
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""

    async def transcribe_bytes(self, audio: bytes, suffix: str = ".webm", language: Optional[str] = None) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio)
            path = tmp.name
        try:
            return await self.transcribe(path, language)
        finally:
            os.unlink(path)

    def get_info(self) -> dict:
        return {
            "service": "Whisper",
            "engine": self.engine,
            "model": self.model_name,
            "status": "ready" if self.is_ready else "not ready",
            "latency_ms": self.last_latency_ms,
            "language": self.last_language,
        }
