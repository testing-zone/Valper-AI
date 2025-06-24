import speech_recognition as sr
import numpy as np
import soundfile as sf
import logging
import os
import tempfile
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_ready = True  # SpeechRecognition is always ready
        
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = False
        logger.info("STT Service initialized with SpeechRecognition")
        
    async def initialize(self):
        """Initialize STT service - no initialization needed for SpeechRecognition"""
        try:
            # Test microphone availability
            self.is_ready = True
            logger.info("SpeechRecognition STT service ready")
        except Exception as e:
            logger.error(f"Error initializing STT service: {e}")
            self.is_ready = False
    
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe audio file to text"""
        if not self.is_ready:
            raise Exception("STT service not initialized")
        
        try:
            # Load audio file with SpeechRecognition
            with sr.AudioFile(audio_file_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record the audio
                audio = self.recognizer.record(source)
            
            # Try multiple recognition engines
            text = await self._try_recognition_engines(audio)
            
            if text:
                logger.info(f"Transcription: {text}")
                return text
            else:
                logger.warning("All recognition engines failed")
                return None
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def transcribe_audio_stream(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data stream to text"""
        if not self.is_ready:
            raise Exception("STT service not initialized")
        
        try:
            # Create temporary file from audio bytes
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Load audio file
                with sr.AudioFile(temp_file_path) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    # Record the audio
                    audio = self.recognizer.record(source)
                
                # Try recognition
                text = await self._try_recognition_engines(audio)
                
                if text:
                    logger.info(f"Stream transcription: {text}")
                    return text
                else:
                    logger.warning("Stream transcription failed")
                    return None
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing audio stream: {e}")
            return None
    
    async def _try_recognition_engines(self, audio) -> Optional[str]:
        """Try multiple recognition engines in order of preference"""
        
        # 1. Try Google Speech Recognition (requires internet)
        try:
            result = self.recognizer.recognize_google(audio, language='en-US')
            logger.info("Used Google Speech Recognition")
            return result
        except sr.RequestError:
            logger.warning("Google Speech Recognition not available (no internet?)")
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
        except Exception as e:
            logger.warning(f"Google Speech Recognition failed: {str(e)}")
        
        # 2. Try Sphinx (offline, requires pocketsphinx)
        try:
            result = self.recognizer.recognize_sphinx(audio)
            logger.info("Used Sphinx (offline) Recognition")
            return result
        except sr.RequestError:
            logger.warning("Sphinx not available (install with: pip install pocketsphinx)")
        except sr.UnknownValueError:
            logger.warning("Sphinx could not understand audio")
        except Exception as e:
            logger.warning(f"Sphinx recognition failed: {str(e)}")
        
        return None
    
    def is_available(self) -> bool:
        """Check if the STT service is available"""
        return self.is_ready
    
    def get_info(self) -> dict:
        """Get information about the STT service"""
        return {
            "service": "SpeechRecognition",
            "engines": ["Google Speech API", "CMU Sphinx (offline)"],
            "sample_rate": 16000,
            "status": "ready" if self.is_ready else "not ready"
        } 