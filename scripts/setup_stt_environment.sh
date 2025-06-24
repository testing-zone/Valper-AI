#!/bin/bash

# Valper AI Assistant - STT Environment Setup Script
# This script sets up a dedicated Python environment for DeepSpeech STT

set -e

echo "🎤 Setting up STT (DeepSpeech) environment..."

# Function to find the best Python 3.8+ version for DeepSpeech
find_python38() {
    for python_cmd in python3.8 python3.9 python3.10 python3; do
        if command -v "$python_cmd" &> /dev/null; then
            version=$($python_cmd --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
            # DeepSpeech works best with Python 3.8-3.10
            if [ "$(printf '%s\n3.8\n' "$version" | sort -V | head -n1)" = "3.8" ] && [ "$(printf '%s\n3.11\n' "$version" | sort -V | head -n1)" = "$version" ]; then
                echo "$python_cmd"
                return 0
            fi
        fi
    done
    return 1
}

# Check if STT environment already exists
if [ -d "venv_stt" ]; then
    echo "🗑️  Removing existing STT environment for clean setup..."
    rm -rf venv_stt
fi

# Find suitable Python version
echo "🔍 Searching for Python 3.8-3.10 for DeepSpeech..."
if PYTHON_CMD=$(find_python38); then
    python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo "✅ Found Python $python_version at: $(which $PYTHON_CMD)"
else
    echo "❌ Python 3.8-3.10 not found!"
    echo "DeepSpeech requires Python 3.8-3.10. Installing Python 3.9..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update
        sudo apt install -y software-properties-common
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt update
        sudo apt install -y python3.9 python3.9-venv python3.9-dev python3.9-distutils
        PYTHON_CMD=python3.9
    else
        echo "Please install Python 3.9 manually and run this script again"
        exit 1
    fi
fi

# Create STT virtual environment
echo "🏗️  Creating STT virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv_stt --prompt "valper-stt"
echo "✅ STT virtual environment created"

# Activate STT environment
echo "🔄 Activating STT environment..."
source venv_stt/bin/activate

# Verify environment
echo "📍 STT Environment info:"
echo "  Python path: $(which python)"
echo "  Python version: $(python --version)"
echo "  Pip path: $(which pip)"

# Upgrade build tools
echo "⬆️  Upgrading build tools..."
python -m pip install --upgrade pip setuptools wheel

# Install system dependencies for DeepSpeech
echo "🔧 Installing system dependencies for STT..."
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
        wget \
        curl
fi

# Install NumPy first (DeepSpeech dependency)
echo "📦 Installing NumPy for DeepSpeech..."
pip install "numpy>=1.14.0,<1.20.0"

# Install DeepSpeech 0.9.3 (stable and available)
echo "📦 Installing DeepSpeech 0.9.3..."
pip install "numpy>=1.14.0,<1.20.0"

# Install DeepSpeech from PyPI - it's available!
echo "🎯 Installing DeepSpeech 0.9.3 from PyPI..."
if pip install deepspeech==0.9.3; then
    echo "✅ DeepSpeech 0.9.3 installed successfully from PyPI"
else
    echo "⚠️  PyPI installation failed, trying alternative sources..."
    
    # Method 1: Try direct wheel installation
    python_version_short=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2 | tr -d '.')
    platform="linux_x86_64"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        platform="macosx_10_10_x86_64"
    fi

    deepspeech_wheel_url="https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-cp${python_version_short}-cp${python_version_short}-${platform}.whl"

    echo "🔗 Trying wheel URL: $deepspeech_wheel_url"
    if pip install "$deepspeech_wheel_url"; then
        echo "✅ DeepSpeech installed from GitHub wheel"
    else
        echo "❌ All DeepSpeech installation methods failed"
        echo "📝 Installing fallback STT service with SpeechRecognition..."
        pip install SpeechRecognition pyaudio
    fi
fi

# Install additional STT dependencies
echo "📦 Installing additional STT dependencies..."
cat > requirements_stt.txt << 'EOF'
# Audio processing
soundfile>=0.10.0
librosa>=0.8.0
scipy>=1.5.0
webrtcvad>=2.0.10

# Utilities
python-dotenv>=0.19.0
asyncio-mqtt>=0.11.0

# For audio streaming
pyaudio>=0.2.11
EOF

pip install -r requirements_stt.txt

# Download DeepSpeech models
echo "📥 Downloading DeepSpeech models..."
mkdir -p models/stt

# Download model files
echo "🔗 Downloading DeepSpeech pre-trained model..."
cd models/stt

if [ ! -f "deepspeech-0.9.3-models.pbmm" ]; then
    wget -O deepspeech-0.9.3-models.pbmm \
        "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm" || \
        echo "⚠️  Could not download model file"
fi

if [ ! -f "deepspeech-0.9.3-models.scorer" ]; then
    wget -O deepspeech-0.9.3-models.scorer \
        "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer" || \
        echo "⚠️  Could not download scorer file"
fi

cd ../..

# Test STT installation
echo "🔍 Testing STT installation..."
python -c "
try:
    import deepspeech
    print('✅ DeepSpeech imported successfully')
    print(f'✅ DeepSpeech version: {deepspeech.__version__}')
except ImportError as e:
    print('❌ DeepSpeech import failed:', e)
    print('📝 Fallback to SpeechRecognition available')

try:
    import soundfile
    print('✅ SoundFile imported successfully')
except ImportError as e:
    print('❌ SoundFile import failed:', e)

try:
    import numpy
    print('✅ NumPy imported successfully')
    print(f'✅ NumPy version: {numpy.__version__}')
except ImportError as e:
    print('❌ NumPy import failed:', e)
"

# Create STT service activation script
echo "📝 Creating STT activation script..."
cat > activate_stt.sh << 'EOF'
#!/bin/bash
echo "🎤 Activating STT (DeepSpeech) environment..."
source venv_stt/bin/activate
echo "✅ STT environment activated!"
echo "📍 Python: $(which python)"
echo "📍 Models directory: $(pwd)/models/stt"
echo ""
EOF
chmod +x activate_stt.sh

echo ""
echo "🎉 STT Environment setup complete!"
echo "================================="
echo "📍 STT Environment: $(pwd)/venv_stt"
echo "📍 Python version: $(python --version)"
echo "📍 Models directory: $(pwd)/models/stt"
echo ""
echo "To activate STT environment:"
echo "  source ./activate_stt.sh"
echo ""
echo "Next: Run ./scripts/setup_tts_environment.sh" 