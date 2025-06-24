#!/bin/bash

# Valper AI Assistant - Cleanup and Setup Master Script
# This script removes old environments and sets up fresh STT and TTS environments

set -e

echo "🧹 Valper AI - Cleanup and Environment Setup"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Please run this script from the Valper-AI root directory"
    exit 1
fi

# Function to cleanup old environments
cleanup_environments() {
    echo "🗑️  Cleaning up existing environments..."
    
    # Remove old virtual environments
    for env_dir in venv venv_stt venv_tts; do
        if [ -d "$env_dir" ]; then
            echo "  🗑️  Removing $env_dir..."
            rm -rf "$env_dir"
        fi
    done
    
    # Remove old activation scripts
    for script in activate_valper.sh activate_stt.sh activate_tts.sh; do
        if [ -f "$script" ]; then
            echo "  🗑️  Removing $script..."
            rm -f "$script"
        fi
    done
    
    # Remove temporary files
    for temp_file in backend/requirements_*.txt; do
        if [ -f "$temp_file" ]; then
            echo "  🗑️  Removing $temp_file..."
            rm -f "$temp_file"
        fi
    done
    
    echo "✅ Cleanup completed"
}

# Function to check system requirements
check_requirements() {
    echo "🔍 Checking system requirements..."
    
    # Check if we're on Linux (required for easy setup)
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        echo "⚠️  This script is optimized for Linux. Manual setup may be required for other OS."
    fi
    
    # Check for sudo access
    if ! sudo -n true 2>/dev/null; then
        echo "🔑 Sudo access required for system dependencies. You may be prompted for password."
    fi
    
    # Check for basic tools
    for tool in wget curl git; do
        if ! command -v "$tool" &> /dev/null; then
            echo "❌ $tool is required but not installed"
            exit 1
        fi
    done
    
    echo "✅ System requirements check passed"
}

# Function to setup STT environment
setup_stt() {
    echo ""
    echo "🎤 Setting up STT (DeepSpeech) Environment"
    echo "=========================================="
    
    if [ -f "scripts/setup_stt_environment.sh" ]; then
        chmod +x scripts/setup_stt_environment.sh
        ./scripts/setup_stt_environment.sh
    else
        echo "❌ STT setup script not found!"
        exit 1
    fi
}

# Function to setup TTS environment
setup_tts() {
    echo ""
    echo "🔊 Setting up TTS (Kokoro) Environment"
    echo "====================================="
    
    if [ -f "scripts/setup_tts_environment.sh" ]; then
        chmod +x scripts/setup_tts_environment.sh
        ./scripts/setup_tts_environment.sh
    else
        echo "❌ TTS setup script not found!"
        exit 1
    fi
}

# Function to update backend services to use the new environments
update_backend_services() {
    echo ""
    echo "🔧 Updating backend services for dual environments..."
    
    # Revert the STT service to use DeepSpeech
    cat > backend/app/services/stt_service.py << 'EOF'
import deepspeech
import numpy as np
import soundfile as sf
import logging
import os
import subprocess
import sys
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.model = None
        self.is_ready = False
        self.model_path = "models/stt/deepspeech-0.9.3-models.pbmm"
        self.scorer_path = "models/stt/deepspeech-0.9.3-models.scorer"
        self.venv_path = "venv_stt"
        
    def _run_in_stt_env(self, command):
        """Run a command in the STT virtual environment"""
        full_command = f"source {self.venv_path}/bin/activate && {command}"
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        return result
        
    async def initialize(self):
        """Initialize DeepSpeech model in STT environment"""
        try:
            if not os.path.exists(self.venv_path):
                logger.error(f"STT environment not found: {self.venv_path}")
                logger.info("Please run ./scripts/setup_stt_environment.sh first")
                return
                
            if not os.path.exists(self.model_path):
                logger.warning(f"Model file not found: {self.model_path}")
                logger.info("Model should be downloaded during STT environment setup")
                return
                
            logger.info("Loading DeepSpeech model in STT environment...")
            
            # Import deepspeech in the STT environment context
            sys.path.insert(0, f"{self.venv_path}/lib/python*/site-packages")
            
            try:
                import deepspeech
                self.model = deepspeech.Model(self.model_path)
                
                if os.path.exists(self.scorer_path):
                    self.model.enableExternalScorer(self.scorer_path)
                    logger.info("External scorer loaded")
                
                self.is_ready = True
                logger.info("DeepSpeech model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading DeepSpeech in STT environment: {e}")
                self.is_ready = False
            
        except Exception as e:
            logger.error(f"Error initializing STT service: {e}")
            self.is_ready = False
    
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe audio file to text using STT environment"""
        if not self.is_ready:
            await self.initialize()
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
            await self.initialize()
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
    
    def is_available(self) -> bool:
        """Check if the STT service is available"""
        return self.is_ready and os.path.exists(self.venv_path)
    
    def get_info(self) -> dict:
        """Get information about the STT service"""
        return {
            "service": "DeepSpeech",
            "version": "0.9.3",
            "model_path": self.model_path,
            "environment": self.venv_path,
            "status": "ready" if self.is_ready else "not ready"
        }
EOF

    # Update TTS service to use Kokoro in TTS environment
    cat > backend/app/services/tts_service.py << 'EOF'
import asyncio
import logging
import os
import tempfile
import subprocess
import sys
from typing import Optional, Generator, Tuple
import soundfile as sf

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.pipeline = None
        self.is_ready = False
        self.venv_path = "venv_tts"
        self.available_voices = ['af_heart', 'af_sky', 'af_light', 'am_adam', 'am_michael']
        
    def _run_in_tts_env(self, command):
        """Run a command in the TTS virtual environment"""
        full_command = f"source {self.venv_path}/bin/activate && {command}"
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        return result
        
    async def initialize(self):
        """Initialize Kokoro TTS pipeline in TTS environment"""
        try:
            if not os.path.exists(self.venv_path):
                logger.error(f"TTS environment not found: {self.venv_path}")
                logger.info("Please run ./scripts/setup_tts_environment.sh first")
                return
                
            logger.info("Loading Kokoro TTS model in TTS environment...")
            
            # Import kokoro in the TTS environment context
            sys.path.insert(0, f"{self.venv_path}/lib/python*/site-packages")
            
            try:
                from kokoro import KPipeline
                self.pipeline = KPipeline(lang_code='a')  # English
                self.is_ready = True
                logger.info("Kokoro TTS model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Kokoro in TTS environment: {e}")
                self.is_ready = False
            
        except Exception as e:
            logger.error(f"Error initializing TTS service: {e}")
            self.is_ready = False
    
    async def synthesize_speech(self, text: str, voice: str = 'af_heart') -> Optional[str]:
        """Synthesize speech from text and return audio file path"""
        if not self.is_ready:
            await self.initialize()
            if not self.is_ready:
                raise Exception("TTS service not initialized")
        
        if voice not in self.available_voices:
            logger.warning(f"Voice {voice} not available, using default 'af_heart'")
            voice = 'af_heart'
        
        try:
            # Generate audio using TTS environment
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
            await self.initialize()
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
    
    def is_available(self) -> bool:
        """Check if the TTS service is available"""
        return self.is_ready and os.path.exists(self.venv_path)
    
    def get_info(self) -> dict:
        """Get information about the TTS service"""
        return {
            "service": "Kokoro TTS",
            "voices": self.available_voices,
            "environment": self.venv_path,
            "status": "ready" if self.is_ready else "not ready"
        }
EOF

    echo "✅ Backend services updated for dual environments"
}

# Main execution
main() {
    echo "Starting Valper AI environment setup..."
    echo "This will create separate environments for STT and TTS models."
    echo ""
    
    # Step 1: Check requirements
    check_requirements
    
    # Step 2: Cleanup old environments
    cleanup_environments
    
    # Step 3: Setup STT environment
    setup_stt
    
    # Step 4: Setup TTS environment  
    setup_tts
    
    # Step 5: Update backend services
    update_backend_services
    
    echo ""
    echo "🎉 Valper AI Environment Setup Complete!"
    echo "========================================"
    echo "📍 STT Environment: $(pwd)/venv_stt (DeepSpeech)"
    echo "📍 TTS Environment: $(pwd)/venv_tts (Kokoro)"
    echo ""
    echo "To activate environments:"
    echo "  STT: source ./activate_stt.sh"
    echo "  TTS: source ./activate_tts.sh"
    echo ""
    echo "Next steps:"
    echo "1. Run testing: ./scripts/test_environments.sh"
    echo "2. Start backend: ./scripts/start_backend.sh"
    echo "3. Start frontend: ./scripts/start_frontend.sh"
    echo ""
    echo "🚀 Ready to test your voice assistant!"
}

# Run main function
main "$@" 