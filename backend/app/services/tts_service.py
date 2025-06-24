import asyncio
import logging
import os
import tempfile
import threading
from typing import Optional, Generator, Tuple
import soundfile as sf
import pyttsx3

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.engine = None
        self.is_ready = False
        
    async def initialize(self):
        """Initialize pyttsx3 TTS engine"""
        try:
            logger.info("Loading pyttsx3 TTS engine...")
            self.engine = pyttsx3.init()
            self._configure_engine()
            self.is_ready = True
            logger.info("pyttsx3 TTS engine loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing TTS service: {e}")
            self.is_ready = False
    
    def _configure_engine(self):
        """Configure the TTS engine settings"""
        if not self.engine:
            return
            
        try:
            # Set speech rate (words per minute)
            self.engine.setProperty('rate', 180)
            
            # Set volume (0.0 to 1.0)
            self.engine.setProperty('volume', 0.9)
            
            # Try to set a nice voice
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.engine.setProperty('voice', voices[0].id)
                    
        except Exception as e:
            logger.warning(f"Could not configure TTS engine: {str(e)}")
    
    async def synthesize_speech(self, text: str, voice: str = 'default') -> Optional[str]:
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
            
            # Use threading to avoid blocking
            def _synthesize():
                try:
                    self.engine.save_to_file(text, temp_file_path)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.error(f"TTS synthesis error: {str(e)}")
            
            # Run synthesis in thread
            thread = threading.Thread(target=_synthesize)
            thread.start()
            thread.join(timeout=30)  # 30 second timeout
            
            # Check if file was created and has content
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
                logger.info(f"Audio saved to: {temp_file_path}")
                return temp_file_path
            else:
                logger.error("TTS synthesis failed - no audio file generated")
                return None
                
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None
    
    async def synthesize_speech_stream(self, text: str, voice: str = 'default') -> Generator[bytes, None, None]:
        """Synthesize speech and yield audio chunks for streaming"""
        if not self.is_ready:
            raise Exception("TTS service not initialized")
        
        try:
            # For pyttsx3, we'll generate the full audio and then stream it
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
        """Get list of available voices"""
        if not self.engine:
            return []
            
        try:
            voices = self.engine.getProperty('voices')
            if voices:
                return [{"id": voice.id, "name": voice.name} for voice in voices]
            return []
        except Exception as e:
            logger.warning(f"Could not get available voices: {str(e)}")
            return []
    
    def is_available(self) -> bool:
        """Check if the TTS service is available"""
        return self.is_ready and self.engine is not None
    
    def get_info(self) -> dict:
        """Get information about the TTS service"""
        info = {
            "service": "pyttsx3",
            "status": "ready" if self.is_available() else "not available"
        }
        
        if self.engine:
            try:
                voices = self.engine.getProperty('voices')
                if voices:
                    current_voice = self.engine.getProperty('voice')
                    voice_info = next((v for v in voices if v.id == current_voice), None)
                    if voice_info:
                        info["voice"] = voice_info.name
                        info["language"] = getattr(voice_info, 'languages', ['unknown'])
                
                info["rate"] = self.engine.getProperty('rate')
                info["volume"] = self.engine.getProperty('volume')
                
            except Exception as e:
                logger.warning(f"Could not get TTS info: {str(e)}")
        
        return info 