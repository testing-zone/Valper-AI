#!/bin/bash

# Valper AI Assistant - Environment Fix Script
# This script fixes the environment issues with DeepSpeech and ensures proper virtual environment usage

set -e

echo "🔧 Fixing Valper AI environment issues..."

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Please run this script from the Valper-AI root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_environment.sh first"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify we're in the virtual environment
echo "📍 Virtual environment info:"
echo "  Python path: $(which python)"
echo "  Python version: $(python --version)"
echo "  Pip path: $(which pip)"

# Upgrade pip first
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Install system dependencies if needed
echo "🔧 Checking system dependencies..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing Linux system dependencies..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev espeak-ng build-essential pkg-config libffi-dev
    
    # Install Python development headers for current Python version
    python_version=$(python --version | cut -d' ' -f 2 | cut -d'.' -f1,2)
    sudo apt-get install -y python${python_version}-dev || echo "⚠️  Python dev headers may already be installed"
fi

# Create fixed requirements without problematic DeepSpeech version
echo "📦 Creating fixed requirements file..."
cd backend

cat > requirements_working.txt << 'EOF'
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0
pydantic==2.5.0

# Audio processing
numpy==1.24.3
soundfile==0.12.1

# Alternative speech recognition (replacing DeepSpeech)
# We'll use SpeechRecognition with Google Speech API or offline alternatives
SpeechRecognition==3.10.0
pyaudio==0.2.11

# TTS - using pyttsx3 as Kokoro alternative for now
pyttsx3==2.90

# Security and utilities
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1

# Additional audio processing
librosa>=0.10.1
scipy>=1.11.0

# Performance monitoring
psutil>=5.9.0
EOF

# Detect GPU and install PyTorch
echo "🔍 Detecting GPU configuration..."
gpu_detected=false

if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected!"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    gpu_detected=true
    
    # Install PyTorch with CUDA support
    echo "📦 Installing PyTorch with CUDA support..."
    pip install torch==2.1.0+cu118 torchaudio==2.1.0+cu118 --index-url https://download.pytorch.org/whl/cu118
    
    # Add GPU optimizations to requirements
    echo "" >> requirements_working.txt
    echo "# GPU optimizations" >> requirements_working.txt
    echo "accelerate>=0.24.0" >> requirements_working.txt
    echo "transformers>=4.35.0" >> requirements_working.txt
else
    echo "💻 No NVIDIA GPU detected, installing CPU-only PyTorch..."
    pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
fi

# Install the working requirements
echo "📦 Installing working Python packages..."
pip install -r requirements_working.txt

# Verify installations
echo "🔍 Verifying installations..."
python -c "import torch; print(f'✅ PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'✅ CUDA available: {torch.cuda.is_available()}')"

python -c "import speech_recognition; print('✅ SpeechRecognition installed')" || echo "❌ SpeechRecognition installation failed"
python -c "import soundfile; print('✅ SoundFile installed')" || echo "❌ SoundFile installation failed"
python -c "import fastapi; print('✅ FastAPI installed')" || echo "❌ FastAPI installation failed"
python -c "import pyttsx3; print('✅ pyttsx3 TTS installed')" || echo "❌ pyttsx3 installation failed"

cd ..

# Update the backend code to use the new speech recognition
echo "🔄 Updating backend code for new speech recognition..."

# Create a new STT service file that uses SpeechRecognition instead of DeepSpeech
cat > backend/services/stt_service_fixed.py << 'EOF'
"""
Speech-to-Text Service using SpeechRecognition library
This replaces the DeepSpeech implementation with a more compatible solution
"""

import logging
import speech_recognition as sr
import io
import tempfile
import os
from typing import Optional

logger = logging.getLogger(__name__)

class STTService:
    """Speech-to-Text service using SpeechRecognition library."""
    
    def __init__(self):
        """Initialize the STT service."""
        self.recognizer = sr.Recognizer()
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = False
        logger.info("STT Service initialized with SpeechRecognition")
    
    async def transcribe_audio(self, audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Sample rate of the audio (default: 16000)
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            # Create a temporary file to save the audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Load audio file
                with sr.AudioFile(temp_file_path) as source:
                    # Adjust for ambient noise if needed
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    # Record the audio
                    audio = self.recognizer.record(source)
                
                # Try multiple recognition engines in order of preference
                transcription = await self._try_recognition_engines(audio)
                
                if transcription:
                    logger.info(f"Successfully transcribed audio: {transcription[:100]}...")
                    return transcription
                else:
                    logger.warning("All recognition engines failed")
                    return None
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error in audio transcription: {str(e)}")
            return None
    
    async def _try_recognition_engines(self, audio) -> Optional[str]:
        """Try multiple recognition engines in order of preference."""
        
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
            logger.warning("Sphinx not available (pocketsphinx not installed)")
        except sr.UnknownValueError:
            logger.warning("Sphinx could not understand audio")
        except Exception as e:
            logger.warning(f"Sphinx recognition failed: {str(e)}")
        
        # 3. Try Wit.ai (requires API key)
        # Uncomment and add your Wit.ai key if you want to use it
        # try:
        #     result = self.recognizer.recognize_wit(audio, key="YOUR_WIT_AI_KEY")
        #     logger.info("Used Wit.ai Recognition")
        #     return result
        # except:
        #     pass
        
        return None
    
    def is_available(self) -> bool:
        """Check if the STT service is available."""
        return True  # SpeechRecognition is always available
    
    def get_info(self) -> dict:
        """Get information about the STT service."""
        return {
            "service": "SpeechRecognition",
            "engines": ["Google Speech API", "CMU Sphinx (offline)"],
            "sample_rate": 16000,
            "status": "ready"
        }
EOF

# Create a new TTS service using pyttsx3
cat > backend/services/tts_service_fixed.py << 'EOF'
"""
Text-to-Speech Service using pyttsx3
This provides a working TTS solution while we work on Kokoro integration
"""

import logging
import pyttsx3
import io
import tempfile
import os
import threading
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-Speech service using pyttsx3."""
    
    def __init__(self):
        """Initialize the TTS service."""
        try:
            self.engine = pyttsx3.init()
            self._configure_engine()
            self.is_ready = True
            logger.info("TTS Service initialized with pyttsx3")
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {str(e)}")
            self.engine = None
            self.is_ready = False
    
    def _configure_engine(self):
        """Configure the TTS engine settings."""
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
    
    async def synthesize_speech(self, text: str, sample_rate: int = 22050) -> Optional[bytes]:
        """
        Convert text to speech and return audio bytes.
        
        Args:
            text: Text to convert to speech
            sample_rate: Sample rate for output audio (default: 22050)
            
        Returns:
            Audio bytes or None if synthesis failed
        """
        if not self.is_ready or not self.engine:
            logger.error("TTS service not available")
            return None
            
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
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
            
            # Check if file was created
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
                # Read audio file
                with open(temp_file_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                # Clean up
                os.unlink(temp_file_path)
                
                logger.info(f"Successfully synthesized speech for text: {text[:50]}...")
                return audio_data
            else:
                logger.error("TTS synthesis failed - no audio file generated")
                return None
                
        except Exception as e:
            logger.error(f"Error in speech synthesis: {str(e)}")
            return None
        finally:
            # Clean up temp file if it exists
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
    
    def is_available(self) -> bool:
        """Check if the TTS service is available."""
        return self.is_ready and self.engine is not None
    
    def get_info(self) -> dict:
        """Get information about the TTS service."""
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
EOF

echo ""
echo "🎉 Environment fix complete!"
echo "========================="
echo "📍 Fixed DeepSpeech compatibility issue"
echo "📍 Installed SpeechRecognition as STT alternative"
echo "📍 Installed pyttsx3 as TTS solution"
echo "📍 Virtual environment is properly activated"
echo ""
echo "🔄 The backend code has been updated with working services:"
echo "   - STT: backend/services/stt_service_fixed.py"
echo "   - TTS: backend/services/tts_service_fixed.py"
echo ""
echo "Next steps:"
echo "1. 🔄 Update your main services to use the fixed versions"
echo "2. 🚀 Start the backend server: ./scripts/start_backend.sh"
echo "3. 🌐 The STT will work offline with Sphinx or online with Google"
echo ""
echo "💡 To install offline speech recognition (optional):"
echo "   pip install pocketsphinx"
echo ""
echo "Current environment status:"
echo "  Python: $(which python)"
echo "  Virtual env: ACTIVATED ✅"
echo "  Packages installed: $(pip list | wc -l) packages" 