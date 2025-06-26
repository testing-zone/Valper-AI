from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.api.routes import router
import os
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Valper AI Assistant",
    description="Voice assistant with speech-to-text and text-to-speech capabilities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for external access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services as global instances
stt_service = STTService()
tts_service = TTSService()

# Share services with router
from app.api import routes
routes.stt_service = stt_service
routes.tts_service = tts_service

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Valper AI Assistant...")
    
    # Initialize STT service
    try:
        await stt_service.initialize()
        logger.info("STT service initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize STT service: {e}")
        # Don't raise the exception, let the service start with STT disabled
    
    # Initialize TTS service
    try:
        await tts_service.initialize()
        logger.info("TTS service initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize TTS service: {e}")
        # Don't raise the exception, let the service start with TTS disabled
    
    logger.info("Valper AI Assistant startup completed!")

@app.get("/")
async def root():
    return {"message": "Valper AI Assistant API", "version": "1.0.0"}

# Include API routes
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 