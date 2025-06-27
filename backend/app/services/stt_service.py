import os
import tempfile
import subprocess
import asyncio
from typing import Optional
import whisper
import logging

logger = logging.getLogger(__name__)

class STTService:
    """Speech-to-Text service using OpenAI Whisper"""
    
    def __init__(self):
        self.model = None
        self.model_name = "base"  # Default model
        self.is_initialized = False
        
    async def initialize(self, model_name: str = "base"):
        """Initialize the Whisper model"""
        try:
            self.model_name = model_name
            logger.info(f"Loading Whisper model: {model_name}")
            
            # Load model in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, whisper.load_model, model_name
            )
            
            self.is_initialized = True
            logger.info(f"Whisper model '{model_name}' loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: bytes, 
                             language: Optional[str] = None,
                             task: str = "transcribe") -> dict:
        """
        Transcribe audio using Whisper
        
        Args:
            audio_data: Audio file bytes
            language: Language code (e.g., 'en', 'es', 'fr'). None for auto-detection
            task: Either 'transcribe' or 'translate'
            
        Returns:
            Dict with transcription results
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._transcribe_file, temp_file_path, language, task
            )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return {
                "success": True,
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "duration": result.get("duration", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "language": "unknown",
                "segments": [],
                "duration": 0.0
            }
    
    def _transcribe_file(self, file_path: str, language: Optional[str], task: str) -> dict:
        """Internal method to transcribe file using Whisper"""
        options = {}
        if language:
            options["language"] = language
        if task == "translate":
            options["task"] = "translate"
            
        result = self.model.transcribe(file_path, **options)
        return result
    
    async def detect_language(self, audio_data: bytes) -> dict:
        """Detect the language of the audio"""
        if not self.is_initialized:
            await self.initialize()
            
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._detect_language_file, temp_file_path
            )
            
            os.unlink(temp_file_path)
            return result
            
        except Exception as e:
            logger.error(f"Error during language detection: {e}")
            return {"language": "unknown", "confidence": 0.0}
    
    def _detect_language_file(self, file_path: str) -> dict:
        """Internal method to detect language"""
        # Load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio(file_path)
        audio = whisper.pad_or_trim(audio)
        
        # Make log-Mel spectrogram and move to the same device as the model
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        
        # Detect the spoken language
        _, probs = self.model.detect_language(mel)
        detected_language = max(probs, key=probs.get)
        confidence = probs[detected_language]
        
        return {
            "language": detected_language,
            "confidence": confidence,
            "all_probabilities": probs
        }
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        # Whisper supports many languages
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", "nl",
            "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", "cs", "ro",
            "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy",
            "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk", "br", "eu",
            "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km",
            "sn", "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", "lo",
            "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl", "mg",
            "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]
    
    def get_available_models(self) -> list:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large", "turbo"]
    
    async def change_model(self, model_name: str):
        """Change the current Whisper model"""
        if model_name not in self.get_available_models():
            raise ValueError(f"Invalid model name. Available models: {self.get_available_models()}")
        
        logger.info(f"Changing model from {self.model_name} to {model_name}")
        await self.initialize(model_name)
    
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "supported_languages": len(self.get_supported_languages()),
            "available_models": self.get_available_models()
        }
    
    @property
    def is_ready(self) -> bool:
        """Check if the STT service is ready"""
        return self.is_initialized
    
    def is_available(self) -> bool:
        """Check if the STT service is available"""
        return self.is_initialized
    
    async def transcribe(self, file_path: str) -> str:
        """
        Transcribe audio file and return just the text
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text or empty string if failed
        """
        try:
            # Read the file as bytes
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # Use the existing transcribe_audio method
            result = await self.transcribe_audio(audio_data)
            
            if result.get("success", False):
                return result.get("text", "").strip()
            else:
                logger.error(f"Transcription failed: {result.get('error', 'Unknown error')}")
                return ""
                
        except Exception as e:
            logger.error(f"Error in transcribe method: {e}")
            return ""
    
    def get_info(self) -> dict:
        """Get information about the STT service"""
        return {
            "service": "OpenAI Whisper",
            "model": self.model_name,
            "status": "ready" if self.is_initialized else "not ready"
        } 