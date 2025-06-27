from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from app.models.schemas import STTRequest, TTSRequest, ConversationResponse
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.services.llm_service import LLMService
import tempfile
import os
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instances (will be set by main.py)
stt_service: Optional[STTService] = None
tts_service: Optional[TTSService] = None
llm_service: Optional[LLMService] = None

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "stt": stt_service.is_ready if stt_service else False,
            "tts": tts_service.is_ready if tts_service else False,
            "llm": llm_service.is_available if llm_service else False
        }
    }

@router.post("/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Convert speech to text"""
    if not stt_service or not stt_service.is_ready:
        raise HTTPException(status_code=503, detail="STT service not available")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process with STT
        text = await stt_service.transcribe(temp_file_path)
        
        # Clean up
        os.unlink(temp_file_path)
        
        if text:
            return {"text": text, "success": True}
        else:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
            
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=f"STT processing error: {str(e)}")

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    if not tts_service or not tts_service.is_ready:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    try:
        audio_path = await tts_service.synthesize(request.text)
        
        if audio_path and os.path.exists(audio_path):
            return FileResponse(
                audio_path,
                media_type="audio/wav",
                filename="response.wav"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
            
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS processing error: {str(e)}")

@router.post("/conversation", response_model=ConversationResponse)
async def conversation(
    audio_file: UploadFile = File(...),
    conversation_history: str = Form(default="[]")
):
    """Complete conversation flow: STT -> LLM -> TTS"""
    try:
        # Parse conversation history
        try:
            history = json.loads(conversation_history)
        except json.JSONDecodeError:
            history = []
        
        # Step 1: STT - Convert audio to text
        if not stt_service or not stt_service.is_ready:
            raise HTTPException(status_code=503, detail="STT service not available")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Transcribe audio
        user_text = await stt_service.transcribe(temp_file_path)
        os.unlink(temp_file_path)  # Clean up
        
        if not user_text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        # Step 2: LLM - Generate response
        if not llm_service or not llm_service.is_available:
            raise HTTPException(status_code=503, detail="LLM service not available")
        
        assistant_text = await llm_service.generate_response(user_text, history)
        
        if not assistant_text:
            raise HTTPException(status_code=500, detail="Failed to generate LLM response")
        
        # Step 3: TTS - Convert response to audio
        if not tts_service or not tts_service.is_ready:
            raise HTTPException(status_code=503, detail="TTS service not available")
        
        audio_path = await tts_service.synthesize(assistant_text)
        
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=500, detail="Failed to generate audio response")
        
        return ConversationResponse(
            user_text=user_text,
            assistant_text=assistant_text,
            audio_path=audio_path,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation error: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation processing error: {str(e)}")

@router.get("/services/status")
async def get_services_status():
    """Get status of all services"""
    return {
        "stt": stt_service.get_info() if stt_service else {"status": "not initialized"},
        "tts": tts_service.get_info() if tts_service else {"status": "not initialized"},
        "llm": llm_service.get_info() if llm_service else {"status": "not initialized"}
    } 