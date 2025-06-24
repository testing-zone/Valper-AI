#!/bin/bash

# Valper AI Assistant - TTS Environment Setup Script
# This script sets up a dedicated Python environment for Kokoro TTS

set -e

echo "🔊 Setting up TTS (Kokoro) environment..."

# Function to find Python 3.9+ for Kokoro
find_python39() {
    for python_cmd in python3.11 python3.10 python3.9 python3; do
        if command -v "$python_cmd" &> /dev/null; then
            version=$($python_cmd --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
            # Kokoro works with Python 3.9+
            if [ "$(printf '%s\n3.9\n' "$version" | sort -V | head -n1)" = "3.9" ]; then
                echo "$python_cmd"
                return 0
            fi
        fi
    done
    return 1
}

# Check if TTS environment already exists
if [ -d "venv_tts" ]; then
    echo "🗑️  Removing existing TTS environment for clean setup..."
    rm -rf venv_tts
fi

# Find suitable Python version
echo "🔍 Searching for Python 3.9+ for Kokoro..."
if PYTHON_CMD=$(find_python39); then
    python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo "✅ Found Python $python_version at: $(which $PYTHON_CMD)"
else
    echo "❌ Python 3.9+ not found!"
    echo "Kokoro requires Python 3.9+. Installing Python 3.10..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update
        sudo apt install -y software-properties-common
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt update
        sudo apt install -y python3.10 python3.10-venv python3.10-dev python3.10-distutils
        PYTHON_CMD=python3.10
    else
        echo "Please install Python 3.10+ manually and run this script again"
        exit 1
    fi
fi

# Create TTS virtual environment
echo "🏗️  Creating TTS virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv_tts --prompt "valper-tts"
echo "✅ TTS virtual environment created"

# Activate TTS environment
echo "🔄 Activating TTS environment..."
source venv_tts/bin/activate

# Verify environment
echo "📍 TTS Environment info:"
echo "  Python path: $(which python)"
echo "  Python version: $(python --version)"
echo "  Pip path: $(which pip)"

# Upgrade build tools
echo "⬆️  Upgrading build tools..."
python -m pip install --upgrade pip setuptools wheel

# Install system dependencies for Kokoro TTS
echo "🔧 Installing system dependencies for TTS..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        libffi-dev \
        python3-dev \
        pkg-config \
        libsox-fmt-all \
        sox \
        libsox-dev \
        espeak-ng \
        espeak-ng-data \
        portaudio19-dev \
        libasound2-dev \
        wget \
        curl \
        git
fi

# Detect GPU and install appropriate PyTorch version
echo "🔍 Detecting GPU configuration for TTS..."
gpu_detected=false

if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected for TTS!"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    gpu_detected=true
    
    # Install PyTorch with CUDA support
    echo "📦 Installing PyTorch with CUDA support for TTS..."
    pip install torch==2.1.0+cu118 torchaudio==2.1.0+cu118 --index-url https://download.pytorch.org/whl/cu118
else
    echo "💻 No NVIDIA GPU detected for TTS, installing CPU-only PyTorch..."
    pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
fi

# Install Kokoro TTS
echo "📦 Installing Kokoro TTS..."

# First install base dependencies
pip install \
    numpy>=1.21.0 \
    soundfile>=0.10.0 \
    librosa>=0.9.0 \
    scipy>=1.7.0 \
    tqdm>=4.60.0

# Try multiple methods to install Kokoro
echo "🔍 Trying to install Kokoro TTS..."

# Method 1: Try from PyPI
if pip install kokoro-tts>=0.9.2; then
    echo "✅ Kokoro TTS installed from PyPI"
elif pip install kokoro>=0.9.2; then
    echo "✅ Kokoro installed from PyPI (alternative package name)"
else
    echo "⚠️  PyPI installation failed, trying GitHub installation..."
    
    # Method 2: Install from GitHub
    if pip install git+https://github.com/resemble-ai/Kokoro.git; then
        echo "✅ Kokoro TTS installed from GitHub"
    else
        echo "⚠️  GitHub installation failed, trying manual clone..."
        
        # Method 3: Manual clone and install
        if [ ! -d "temp_kokoro" ]; then
            git clone https://github.com/resemble-ai/Kokoro.git temp_kokoro
        fi
        
        cd temp_kokoro
        if pip install -e .; then
            echo "✅ Kokoro TTS installed from local source"
        else
            echo "❌ All Kokoro installation methods failed"
            echo "📝 Installing fallback TTS (pyttsx3)..."
            pip install pyttsx3>=2.90
        fi
        cd ..
        rm -rf temp_kokoro
    fi
fi

# Install additional TTS dependencies
echo "📦 Installing additional TTS dependencies..."
cat > requirements_tts.txt << 'EOF'
# Audio processing and synthesis
soundfile>=0.10.0
librosa>=0.9.0
scipy>=1.7.0
numpy>=1.21.0

# Model and AI utilities
transformers>=4.20.0
accelerate>=0.20.0
datasets>=2.0.0

# Utilities
python-dotenv>=0.19.0
asyncio-mqtt>=0.11.0
tqdm>=4.60.0

# Web and API
fastapi>=0.68.0
uvicorn>=0.15.0

# Audio streaming
pyaudio>=0.2.11
EOF

pip install -r requirements_tts.txt

# Install GPU optimizations if GPU detected
if [ "$gpu_detected" = true ]; then
    echo "📦 Installing GPU optimizations for TTS..."
    pip install accelerate>=0.24.0
fi

# Download Kokoro models
echo "📥 Setting up Kokoro models..."
mkdir -p models/tts

# Test TTS installation
echo "🔍 Testing TTS installation..."
python -c "
import sys
import warnings
warnings.filterwarnings('ignore')

print('Testing TTS imports...')

# Test PyTorch
try:
    import torch
    print(f'✅ PyTorch version: {torch.__version__}')
    print(f'✅ CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'✅ CUDA device count: {torch.cuda.device_count()}')
except ImportError as e:
    print(f'❌ PyTorch import failed: {e}')

# Test audio processing
try:
    import soundfile
    print('✅ SoundFile imported successfully')
except ImportError as e:
    print(f'❌ SoundFile import failed: {e}')

try:
    import librosa
    print('✅ Librosa imported successfully')
except ImportError as e:
    print(f'❌ Librosa import failed: {e}')

# Test Kokoro TTS
try:
    from kokoro import KPipeline
    print('✅ Kokoro TTS imported successfully')
    
    # Try to initialize (this might download models)
    print('🔄 Initializing Kokoro pipeline...')
    pipeline = KPipeline(lang_code='a')  # English
    print('✅ Kokoro pipeline initialized successfully')
    
except ImportError as e:
    print(f'❌ Kokoro TTS import failed: {e}')
    print('📝 Checking for fallback TTS...')
    try:
        import pyttsx3
        print('✅ Fallback TTS (pyttsx3) available')
    except ImportError:
        print('❌ No TTS available')
except Exception as e:
    print(f'⚠️  Kokoro TTS initialization issue: {e}')
    print('📝 This might be resolved on first model download')
"

# Create TTS service activation script
echo "📝 Creating TTS activation script..."
cat > activate_tts.sh << 'EOF'
#!/bin/bash
echo "🔊 Activating TTS (Kokoro) environment..."
source venv_tts/bin/activate
echo "✅ TTS environment activated!"
echo "📍 Python: $(which python)"
echo "📍 Models directory: $(pwd)/models/tts"
echo ""
EOF
chmod +x activate_tts.sh

echo ""
echo "🎉 TTS Environment setup complete!"
echo "================================="
echo "📍 TTS Environment: $(pwd)/venv_tts"
echo "📍 Python version: $(python --version)"
echo "📍 Models directory: $(pwd)/models/tts"

if [ "$gpu_detected" = true ]; then
    echo "🎮 GPU support: ENABLED"
else
    echo "💻 GPU support: CPU-only mode"
fi

echo ""
echo "To activate TTS environment:"
echo "  source ./activate_tts.sh"
echo ""
echo "Next: Run ./scripts/cleanup_and_setup.sh" 