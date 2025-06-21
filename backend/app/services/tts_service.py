import asyncio
import logging
import os
import tempfile
from typing import Optional, Generator, Tuple
import soundfile as sf
import torch

try:
    from kokoro import KPipeline
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False
    logging.warning("Kokoro not available. Install with: pip install kokoro>=0.9.2")

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.pipeline = None
        self.is_ready = False
        self.available_voices = ['af_heart', 'af_sky', 'af_light', 'am_adam', 'am_michael']
        
    async def initialize(self):
        """Initialize Kokoro TTS pipeline"""
        if not KOKORO_AVAILABLE:
            logger.error("Kokoro TTS is not available")
            return
            
        try:
            logger.info("Loading Kokoro TTS model...")
            self.pipeline = KPipeline(lang_code='a')  # English
            self.is_ready = True
            logger.info("Kokoro TTS model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing TTS service: {e}")
            self.is_ready = False
    
    async def synthesize_speech(self, text: str, voice: str = 'af_heart') -> Optional[str]:
        """Synthesize speech from text and return audio file path"""
        if not self.is_ready:
            raise Exception("TTS service not initialized")
        
        if voice not in self.available_voices:
            logger.warning(f"Voice {voice} not available, using default 'af_heart'")
            voice = 'af_heart'
        
        try:
            # Generate audio
            generator = self.pipeline(text, voice=voice)
            
            # Get the first (and usually only) audio chunk
            for i, (gs, ps, audio) in enumerate(generator):
                logger.info(f"Generated audio chunk {i}: {gs}, {ps}")
                
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.wav',
                    dir='temp/audio'
                )
                
                # Ensure temp directory exists
                os.makedirs('temp/audio', exist_ok=True)
                
                # Save audio to file
                sf.write(temp_file.name, audio, 24000)
                temp_file.close()
                
                logger.info(f"Audio saved to: {temp_file.name}")
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None
    
    async def synthesize_speech_stream(self, text: str, voice: str = 'af_heart') -> Generator[bytes, None, None]:
        """Synthesize speech and yield audio chunks for streaming"""
        if not self.is_ready:
            raise Exception("TTS service not initialized")
        
        if voice not in self.available_voices:
            voice = 'af_heart'
        
        try:
            generator = self.pipeline(text, voice=voice)
            
            for i, (gs, ps, audio) in enumerate(generator):
                # Convert audio to bytes
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav')
                sf.write(temp_file.name, audio, 24000)
                
                with open(temp_file.name, 'rb') as f:
                    audio_bytes = f.read()
                
                temp_file.close()
                yield audio_bytes
                
        except Exception as e:
            logger.error(f"Error streaming speech: {e}")
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        return self.available_voices 