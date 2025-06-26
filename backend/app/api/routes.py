from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
import tempfile
import os
import logging
import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Services will be injected from main.py
stt_service = None
tts_service = None

class TTSRequest(BaseModel):
    text: str
    voice: str = 'af_heart'

class ConversationRequest(BaseModel):
    message: str

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the API is working"""
    return {
        "message": "API is working!",
        "timestamp": str(datetime.datetime.now()),
        "stt_available": stt_service is not None,
        "tts_available": tts_service is not None
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for API monitoring"""
    return {
        "status": "healthy",
        "stt_ready": stt_service.is_ready if stt_service else False,
        "tts_ready": tts_service.is_ready if tts_service else False
    }

@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert speech to text"""
    if not stt_service:
        raise HTTPException(status_code=503, detail="STT service not available")
    
    if not stt_service.is_ready:
        raise HTTPException(status_code=503, detail="STT service not ready")
    
    if not audio.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Read audio file content
        content = await audio.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Transcribe audio using bytes
        result = await stt_service.transcribe_audio(content)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to transcribe audio"))
        
        return {"text": result["text"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in STT endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    if not tts_service:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    if not tts_service.is_ready:
        raise HTTPException(status_code=503, detail="TTS service not ready")
    
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        audio_file_path = await tts_service.synthesize_speech(request.text, request.voice)
        
        if audio_file_path is None:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")
        
        if not os.path.exists(audio_file_path):
            raise HTTPException(status_code=500, detail="Generated audio file not found")
        
        return FileResponse(
            audio_file_path,
            media_type='audio/wav',
            filename='speech.wav'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in TTS endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/voices")
async def get_voices():
    """Get available TTS voices"""
    if not tts_service:
        return {"voices": []}
    return {"voices": tts_service.get_available_voices()}

@router.post("/conversation")
async def conversation(request: ConversationRequest):
    """Simple conversation endpoint (placeholder for future LLM integration)"""
    # This is a simple echo for now - you can integrate with an LLM later
    response_text = f"You said: {request.message}. This is Valper responding!"
    
    if not tts_service or not tts_service.is_ready:
        return {"text_response": response_text, "audio_url": None}
    
    try:
        audio_file_path = await tts_service.synthesize_speech(response_text)
        
        return {
            "text_response": response_text,
            "audio_url": f"/api/v1/audio/{os.path.basename(audio_file_path)}"
        }
        
    except Exception as e:
        logger.error(f"Error in conversation endpoint: {e}")
        return {"text_response": response_text, "audio_url": None}

@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio files"""
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, 'temp', 'audio', filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='audio/wav')
    else:
        raise HTTPException(status_code=404, detail="Audio file not found") 