from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech", max_length=1000)
    voice: str = Field(default='af_heart', description="Voice to use for synthesis")

class TTSResponse(BaseModel):
    audio_url: str
    duration: Optional[float] = None

class STTResponse(BaseModel):
    text: str
    confidence: Optional[float] = None

class ConversationRequest(BaseModel):
    message: str = Field(..., description="User message", max_length=500)
    session_id: Optional[str] = None

class ConversationResponse(BaseModel):
    text_response: str
    audio_url: Optional[str] = None
    session_id: Optional[str] = None

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