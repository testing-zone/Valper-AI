from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import UploadFile

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech", max_length=5000)
    voice: str = Field(default='af_heart', description="Voice to use for synthesis")

class TTSResponse(BaseModel):
    audio_url: str
    duration: Optional[float] = None

class STTResponse(BaseModel):
    text: str
    confidence: Optional[float] = None



class ConversationResponse(BaseModel):
    user_text: str
    assistant_text: str
    audio_path: str
    success: bool

class HealthResponse(BaseModel):
    status: str
    stt_ready: bool
    tts_ready: bool
    timestamp: datetime = Field(default_factory=datetime.now)

class VoiceInfo(BaseModel):
    id: str
    name: str
    gender: str
    description: Optional[str] = None

class VoicesResponse(BaseModel):
    voices: List[VoiceInfo]

class STTRequest(BaseModel):
    """Request model for STT"""
    pass

class ServiceStatus(BaseModel):
    """Service status information"""
    service: str
    status: str
    details: Optional[Dict] = None 