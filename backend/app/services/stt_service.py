import deepspeech
import numpy as np
import soundfile as sf
import logging
import os
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.model = None
        self.is_ready = False
        self.model_path = "models/deepspeech-0.9.3-models.pbmm"
        self.scorer_path = "models/deepspeech-0.9.3-models.scorer"
        
    async def initialize(self):
        """Initialize DeepSpeech model"""
        try:
            if not os.path.exists(self.model_path):
                logger.warning(f"Model file not found: {self.model_path}")
                logger.info("Please download the DeepSpeech model using setup_models.sh")
                return
                
            logger.info("Loading DeepSpeech model...")
            self.model = deepspeech.Model(self.model_path)
            
            if os.path.exists(self.scorer_path):
                self.model.enableExternalScorer(self.scorer_path)
                logger.info("External scorer loaded")
            
            self.is_ready = True
            logger.info("DeepSpeech model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing STT service: {e}")
            self.is_ready = False
    
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe audio file to text"""
        if not self.is_ready:
            raise Exception("STT service not initialized")
        
        try:
            # Read audio file
            audio, sample_rate = sf.read(audio_file_path, dtype=np.int16)
            
            # DeepSpeech expects 16kHz sample rate
            if sample_rate != 16000:
                logger.warning(f"Audio sample rate is {sample_rate}, DeepSpeech expects 16000Hz")
            
            # Transcribe
            text = self.model.stt(audio)
            
            logger.info(f"Transcription: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def transcribe_audio_stream(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data stream to text"""
        if not self.is_ready:
            raise Exception("STT service not initialized")
        
        try:
            # Convert bytes to numpy array
            audio = np.frombuffer(audio_data, dtype=np.int16)
            
            # Transcribe
            text = self.model.stt(audio)
            
            logger.info(f"Stream transcription: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing audio stream: {e}")
            return None 