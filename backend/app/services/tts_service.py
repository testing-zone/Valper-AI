import asyncio
import logging
import os
import tempfile
from typing import Optional, Generator
import soundfile as sf
import torch
from kokoro import KPipeline

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.pipeline = None
        self.is_ready = False
        
    async def initialize(self):
        """Initialize Kokoro TTS pipeline"""
        try:
            logger.info("Loading Kokoro TTS pipeline...")
            # Initialize Kokoro pipeline with language code 'a' (English)
            self.pipeline = KPipeline(lang_code='a')
            self.is_ready = True
            logger.info("Kokoro TTS pipeline loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Kokoro TTS service: {e}")
            self.is_ready = False
    
    async def synthesize_speech(self, text: str, voice: str = 'af_heart') -> Optional[str]:
        """Synthesize speech from text and return audio file path"""
        if not self.is_ready:
            raise Exception("TTS service not initialized")
        
        try:
            # Ensure temp directory exists
            os.makedirs('temp/audio', exist_ok=True)
            
            # Create temporary file for audio output
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.wav',
                dir='temp/audio'
            )
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Generate audio using Kokoro
            logger.info(f"Generating audio for text: {text[:50]}...")
            generator = self.pipeline(text, voice=voice)
            
            # Get the first (and usually only) audio output
            for i, (gs, ps, audio) in enumerate(generator):
                logger.info(f"Generated audio chunk {i}, shape: {audio.shape}")
                # Save audio using soundfile (24kHz sample rate for Kokoro)
                sf.write(temp_file_path, audio, 24000)
                break  # Only use the first generated audio
            
            # Check if file was created and has content
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
                logger.info(f"Audio saved to: {temp_file_path}, size: {os.path.getsize(temp_file_path)} bytes")
                return temp_file_path
            else:
                logger.error("TTS synthesis failed - no audio file generated")
                return None
                
        except Exception as e:
            logger.error(f"Error synthesizing speech with Kokoro: {e}")
            return None
    
    async def synthesize_speech_stream(self, text: str, voice: str = 'af_heart') -> Generator[bytes, None, None]:
        """Synthesize speech and yield audio chunks for streaming"""
        if not self.is_ready:
            raise Exception("TTS service not initialized")
        
        try:
            # For Kokoro, we'll generate the full audio and then stream it
            audio_file_path = await self.synthesize_speech(text, voice)
            
            if audio_file_path and os.path.exists(audio_file_path):
                # Read file in chunks
                with open(audio_file_path, 'rb') as f:
                    chunk_size = 4096
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                
                # Clean up temp file
                try:
                    os.unlink(audio_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error streaming speech: {e}")
    
    def get_available_voices(self) -> list:
        """Get list of available Kokoro voices"""
        # Common Kokoro voices
        return [
            {"id": "af_heart", "name": "African Female Heart"},
            {"id": "af_sky", "name": "African Female Sky"},
            {"id": "af_bella", "name": "African Female Bella"},
            {"id": "af_sarah", "name": "African Female Sarah"},
            {"id": "am_adam", "name": "African Male Adam"},
            {"id": "am_michael", "name": "African Male Michael"},
            {"id": "bf_emma", "name": "British Female Emma"},
            {"id": "bf_isabella", "name": "British Female Isabella"},
            {"id": "bm_george", "name": "British Male George"},
            {"id": "bm_lewis", "name": "British Male Lewis"}
        ]
    
    def is_available(self) -> bool:
        """Check if the TTS service is available"""
        return self.is_ready and self.pipeline is not None
    
    def get_info(self) -> dict:
        """Get information about the TTS service"""
        return {
            "service": "Kokoro TTS",
            "status": "ready" if self.is_available() else "not available",
            "model": "Kokoro 82M parameters",
            "sample_rate": "24kHz",
            "available_voices": len(self.get_available_voices())
        } 