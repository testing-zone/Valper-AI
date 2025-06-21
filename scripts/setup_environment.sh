#!/bin/bash

# Valper AI Assistant - Environment Setup Script
# This script sets up the Python 3.11+ environment and installs all dependencies with GPU support

set -e

echo "🐍 Setting up Valper AI Assistant environment with Python 3.11+..."

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

# Function to compare versions
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

if ! version_ge "$python_version" "$required_version"; then
    echo "❌ Python 3.11+ required, found Python $python_version"
    echo "Please install Python 3.11+ and try again"
    
    # Provide installation instructions based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "For macOS, install via:"
        echo "  brew install python@3.11"
        echo "  Or download from: https://www.python.org/downloads/"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "For Ubuntu/Debian, install via:"
        echo "  sudo apt update"
        echo "  sudo apt install python3.11 python3.11-venv python3.11-dev"
    fi
    exit 1
fi

echo "✅ Python $python_version found (≥ 3.11 required)"

# Remove existing virtual environment if it exists to ensure clean setup
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment for clean setup..."
    rm -rf venv
fi

# Create isolated virtual environment with Python 3.11+
echo "🏗️  Creating isolated virtual environment..."
python3 -m venv venv --prompt "valper-ai"
echo "✅ Virtual environment created at: $(pwd)/venv"

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify we're in the correct environment
echo "📍 Virtual environment info:"
echo "  Python path: $(which python)"
echo "  Python version: $(python --version)"
echo "  Pip path: $(which pip)"

# Upgrade pip, setuptools, and wheel to latest versions
echo "⬆️  Upgrading build tools..."
pip install --upgrade pip setuptools wheel

# Detect GPU and install appropriate PyTorch version
echo "🔍 Detecting GPU configuration..."
gpu_detected=false

if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected!"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    gpu_detected=true
    
    # Install PyTorch with CUDA support
    echo "📦 Installing PyTorch with CUDA support..."
    pip install torch==2.1.0+cu118 torchaudio==2.1.0+cu118 --index-url https://download.pytorch.org/whl/cu118
else
    echo "💻 No NVIDIA GPU detected, installing CPU-only PyTorch..."
    pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
fi

# Install system dependencies for audio processing
echo "🔧 Installing system dependencies..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        echo "Installing macOS dependencies via Homebrew..."
        brew install portaudio espeak-ng || echo "⚠️  Some dependencies may already be installed"
    else
        echo "⚠️  Homebrew not found. Please install manually:"
        echo "  brew install portaudio espeak-ng"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Installing Linux dependencies..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev espeak-ng python3.11-dev build-essential
    elif command -v yum &> /dev/null; then
        sudo yum install -y portaudio-devel espeak-ng python3-devel gcc
    else
        echo "⚠️  Package manager not detected. Install manually: portaudio-dev, espeak-ng"
    fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend

# Create a requirements file with exact versions for stability
cat > requirements_fixed.txt << 'EOF'
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0
pydantic==2.5.0

# Audio processing
numpy==1.24.3
soundfile==0.12.1

# AI models
deepspeech==0.9.3
kokoro>=0.9.2

# Security and utilities
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1

# Additional GPU optimizations (if GPU detected)
EOF

if [ "$gpu_detected" = true ]; then
    echo "# GPU optimizations" >> requirements_fixed.txt
    echo "accelerate>=0.24.0" >> requirements_fixed.txt
    echo "transformers>=4.35.0" >> requirements_fixed.txt
fi

# Install all dependencies
pip install -r requirements_fixed.txt

# Verify critical installations
echo "🔍 Verifying installations..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
if [ "$gpu_detected" = true ]; then
    python -c "import torch; print(f'CUDA device count: {torch.cuda.device_count()}')" || echo "⚠️  CUDA not properly configured"
fi

python -c "import deepspeech; print('✅ DeepSpeech installed')" || echo "❌ DeepSpeech installation failed"
python -c "import soundfile; print('✅ SoundFile installed')" || echo "❌ SoundFile installation failed"

# Try to import Kokoro (might fail initially, that's OK)
python -c "
try:
    from kokoro import KPipeline
    print('✅ Kokoro TTS installed and importable')
except ImportError as e:
    print('⚠️  Kokoro TTS import issue (will be resolved on first use):', str(e))
except Exception as e:
    print('⚠️  Kokoro TTS other issue:', str(e))
"

cd ..

# Create necessary directories with proper permissions
echo "📁 Creating project directories..."
mkdir -p models temp/audio logs
chmod 755 models temp temp/audio logs

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📄 Creating .env configuration file..."
    cat > .env << 'EOF'
# Valper AI Assistant Environment Configuration

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Model Paths
MODELS_DIR=models
TEMP_AUDIO_DIR=temp/audio

# Audio Settings
SAMPLE_RATE=16000

# Logging
LOG_LEVEL=INFO

# Frontend
REACT_APP_API_URL=http://localhost:8000
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Create a script to easily activate the environment
echo "📝 Creating activation script..."
cat > activate_valper.sh << 'EOF'
#!/bin/bash
# Valper AI Assistant - Environment Activation Script
echo "🚀 Activating Valper AI environment..."
source venv/bin/activate
echo "✅ Environment activated!"
echo "📍 Python: $(which python)"
echo "📍 Current directory: $(pwd)"
echo ""
echo "Available commands:"
echo "  ./scripts/setup_models.sh    - Download AI models"
echo "  ./scripts/start_backend.sh   - Start backend server"
echo "  ./scripts/start_frontend.sh  - Start frontend (in another terminal)"
echo ""
EOF
chmod +x activate_valper.sh

# Final verification and summary
echo ""
echo "🎉 Environment setup complete!"
echo "=========================="
echo "📍 Project location: $(pwd)"
echo "📍 Virtual environment: $(pwd)/venv"
echo "📍 Python version: $(python --version)"
echo "📍 Pip packages installed: $(pip list | wc -l) packages"

if [ "$gpu_detected" = true ]; then
    echo "🎮 GPU support: ENABLED"
    echo "   CUDA version: $(python -c 'import torch; print(torch.version.cuda)' 2>/dev/null || echo 'Not available')"
else
    echo "💻 GPU support: CPU-only mode"
fi

echo ""
echo "Next steps:"
echo "1. 🔄 To activate environment in the future:"
echo "   source ./activate_valper.sh"
echo ""
echo "2. 📥 Download AI models:"
echo "   ./scripts/setup_models.sh"
echo ""
echo "3. 🚀 Start the application:"
echo "   ./scripts/start_backend.sh     (Terminal 1)"
echo "   ./scripts/start_frontend.sh    (Terminal 2)"
echo ""
echo "4. 🌐 Access the interface:"
echo "   Frontend: http://localhost:3000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "💡 Environment is isolated and won't conflict with other projects!"

# Save environment info for troubleshooting
echo "🔍 Saving environment info for troubleshooting..."
cat > logs/environment_info.txt << EOF
Valper AI Environment Setup Information
======================================
Date: $(date)
OS: $OSTYPE
Python version: $(python --version)
Pip version: $(pip --version)
GPU detected: $gpu_detected
Virtual environment: $(pwd)/venv

Installed packages:
$(pip list)

GPU Information:
$(nvidia-smi 2>/dev/null || echo "No NVIDIA GPU detected")

System Information:
$(uname -a)
EOF

echo "📝 Environment info saved to: logs/environment_info.txt" 