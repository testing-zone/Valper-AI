import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import scheduler
from app.api import routes
from app.api.routes import router
from app.integrations import discord_bot
from app.tools import notify
from app.core import db
from app.core.config import ROOT_DIR, settings
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

stt_service = STTService()
tts_service = TTSService()
routes.stt_service = stt_service
routes.tts_service = tts_service
notify.tts = tts_service
discord_bot.stt = stt_service
discord_bot.tts = tts_service


async def _load_speech_models():
    """Heavy models load in the background so the API and scheduler are up immediately."""
    for name, service in (("STT", stt_service), ("TTS", tts_service)):
        try:
            await service.initialize()
        except Exception as e:
            logger.error(f"{name} disabled: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.NAME}...")
    db.init()
    scheduler.start()
    loader = asyncio.create_task(_load_speech_models())
    await discord_bot.start()
    yield
    loader.cancel()
    await discord_bot.stop()
    scheduler.shutdown()


app = FastAPI(title=f"{settings.NAME} — asistente personal", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api")

# Serve the built React app (npm run build) so everything runs on one port
FRONTEND_BUILD = ROOT_DIR / "frontend" / "build"
if FRONTEND_BUILD.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {"message": f"{settings.NAME} API", "version": "3.0.0", "ui": "run: npm run build in frontend/"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
