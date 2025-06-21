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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
stt_service = STTService()
tts_service = TTSService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Valper AI Assistant...")
    await stt_service.initialize()
    await tts_service.initialize()
    logger.info("Services initialized successfully!")

@app.get("/")
async def root():
    return {"message": "Valper AI Assistant API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "stt_ready": stt_service.is_ready,
        "tts_ready": tts_service.is_ready
    }

# Include API routes
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 