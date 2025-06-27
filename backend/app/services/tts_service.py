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
    
    def _split_text(self, text: str, max_length: int = 800) -> list:
        """Split text into smaller chunks for better TTS processing"""
        if len(text) <= max_length:
            return [text]
        
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Add period back if it's not the last sentence
            sentence = sentence.strip()
            if not sentence.endswith('.') and sentence != sentences[-1]:
                sentence += '.'
            
            # Check if adding this sentence would exceed the limit
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # If current chunk is not empty, save it
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    # If single sentence is too long, force split it
                    words = sentence.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) + 1 <= max_length:
                            if current_chunk:
                                current_chunk += " " + word
                            else:
                                current_chunk = word
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = word
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    async def synthesize_speech(self, text: str, voice: str = 'af_heart') -> Optional[str]:
        """Synthesize speech from text and return audio file path"""
        if not self.is_ready:
            raise Exception("TTS service not initialized")
        
        try:
            # Get the current working directory and create temp directory
            current_dir = os.getcwd()
            temp_dir = os.path.join(current_dir, 'temp', 'audio')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create temporary file for audio output
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.wav',
                dir=temp_dir
            )
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Split text into smaller chunks for better processing
            text_chunks = self._split_text(text)
            logger.info(f"Text split into {len(text_chunks)} chunks")
            logger.info(f"Full text length: {len(text)} characters")
            
            # Process each text chunk and collect audio
            all_audio_chunks = []
            
            for chunk_idx, text_chunk in enumerate(text_chunks):
                logger.info(f"Processing text chunk {chunk_idx + 1}/{len(text_chunks)}: {text_chunk[:50]}...")
                
                # Generate audio for this text chunk
                generator = self.pipeline(text_chunk, voice=voice)
                
                # Collect audio for this text chunk
                chunk_audio_parts = []
                for i, (gs, ps, audio) in enumerate(generator):
                    logger.info(f"Generated audio part {i} for chunk {chunk_idx + 1}, shape: {audio.shape}")
                    chunk_audio_parts.append(audio)
                
                # Concatenate audio parts for this chunk
                if len(chunk_audio_parts) > 1:
                    import numpy as np
                    chunk_audio = np.concatenate(chunk_audio_parts, axis=0)
                elif len(chunk_audio_parts) == 1:
                    chunk_audio = chunk_audio_parts[0]
                else:
                    logger.warning(f"No audio generated for chunk {chunk_idx + 1}")
                    continue
                
                all_audio_chunks.append(chunk_audio)
                logger.info(f"Chunk {chunk_idx + 1} audio shape: {chunk_audio.shape}")
            
            # Concatenate all chunks into final audio
            if len(all_audio_chunks) > 1:
                import numpy as np
                final_audio = np.concatenate(all_audio_chunks, axis=0)
                logger.info(f"Final concatenated audio shape: {final_audio.shape}")
            elif len(all_audio_chunks) == 1:
                final_audio = all_audio_chunks[0]
                logger.info(f"Single chunk final audio shape: {final_audio.shape}")
            else:
                logger.error("No audio chunks generated")
                return None
            
            # Save the final concatenated audio
            sf.write(temp_file_path, final_audio, 24000)
            
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
    
    async def synthesize(self, text: str, voice: str = 'af_heart') -> Optional[str]:
        """
        Synthesize speech from text and return audio file path
        This is an alias for synthesize_speech for compatibility
        
        Args:
            text: Text to synthesize
            voice: Voice to use for synthesis
            
        Returns:
            Path to the generated audio file or None if failed
        """
        return await self.synthesize_speech(text, voice)
    
    def get_info(self) -> dict:
        """Get information about the TTS service"""
        return {
            "service": "Kokoro TTS",
            "status": "ready" if self.is_available() else "not available",
            "model": "Kokoro 82M parameters",
            "sample_rate": "24kHz",
            "available_voices": len(self.get_available_voices())
        } 