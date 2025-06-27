#!/bin/bash

# Valper AI Assistant - Environment Setup Script
# This script sets up the Python 3.11+ environment and installs all dependencies with GPU support

set -e

echo "🐍 Setting up Valper AI Assistant environment with Python 3.11+..."

# Function to find the best Python 3.11+ version
find_python311() {
    # Try different Python 3.11+ executables in order of preference
    for python_cmd in python3.12 python3.11 python3; do
        if command -v "$python_cmd" &> /dev/null; then
            version=$($python_cmd --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
            # Check if version is >= 3.11
            if [ "$(printf '%s\n3.11\n' "$version" | sort -V | head -n1)" = "3.11" ]; then
                echo "$python_cmd"
                return 0
            fi
        fi
    done
    return 1
}

# Find Python 3.11+
echo "🔍 Searching for Python 3.11+..."
if PYTHON_CMD=$(find_python311); then
    python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo "✅ Found Python $python_version at: $(which $PYTHON_CMD)"
else
    echo "❌ Python 3.11+ not found!"
    echo ""
    echo "📦 Installing Python 3.11+ for your system..."
    
    # Provide installation instructions and try to install automatically
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "For macOS, installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install python@3.11 || echo "⚠️  Manual installation may be needed"
        else
            echo "❌ Homebrew not found. Please install manually:"
            echo "  1. Install Homebrew: https://brew.sh/"
            echo "  2. Run: brew install python@3.11"
            echo "  3. Or download from: https://www.python.org/downloads/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "For Linux, installing Python 3.11..."
        if command -v apt-get &> /dev/null; then
            echo "📥 Installing Python 3.11 via apt..."
            sudo apt update
            sudo apt install -y software-properties-common
            
            # Check if we need to add deadsnakes PPA
            if ! apt-cache show python3.11 &> /dev/null; then
                echo "📦 Adding deadsnakes PPA for Python 3.11..."
                sudo add-apt-repository ppa:deadsnakes/ppa -y
                sudo apt update
            fi
            
            sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils
            echo "✅ Python 3.11 installation completed!"
            
        elif command -v yum &> /dev/null; then
            echo "📥 Installing Python 3.11 via yum..."
            sudo yum install -y python3.11 python3.11-devel
        else
            echo "❌ Package manager not detected. Please install Python 3.11 manually:"
            echo "  Ubuntu/Debian: sudo apt install python3.11 python3.11-venv python3.11-dev"
            echo "  CentOS/RHEL: sudo yum install python3.11 python3.11-devel"
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install Python 3.11+ manually:"
        echo "  Download from: https://www.python.org/downloads/"
        exit 1
    fi
    
    # Try to find Python again after installation
    echo "🔍 Re-checking for Python 3.11+ after installation..."
    if PYTHON_CMD=$(find_python311); then
        python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
        echo "✅ Found Python $python_version at: $(which $PYTHON_CMD)"
    else
        echo "❌ Python 3.11+ still not found after installation attempt."
        echo "Please check the installation and try again, or install manually:"
        echo "  Ubuntu: sudo apt install python3.11 python3.11-venv python3.11-dev"
        echo "  macOS: brew install python@3.11"
        exit 1
    fi
fi

# Remove existing virtual environment if it exists to ensure clean setup
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment for clean setup..."
    rm -rf venv
fi

# Create isolated virtual environment with Python 3.11+
echo "🏗️  Creating isolated virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv --prompt "valper-ai"
echo "✅ Virtual environment created at: $(pwd)/venv"

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify we're in the correct environment and using the right Python
echo "📍 Virtual environment info:"
echo "  Python path: $(which python)"
echo "  Python version: $(python --version)"
echo "  Pip path: $(which pip)"

# Verify Python version in virtual environment
venv_python_version=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(printf '%s\n3.11\n' "$venv_python_version" | sort -V | head -n1)" != "3.11" ]; then
    echo "❌ Virtual environment is not using Python 3.11+!"
    echo "Current version: $venv_python_version"
    exit 1
fi

# Upgrade pip, setuptools, and wheel to latest versions
echo "⬆️  Upgrading build tools..."
python -m pip install --upgrade pip setuptools wheel

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
        sudo apt-get install -y portaudio19-dev espeak-ng build-essential
        
        # Install development headers for the Python version we're using
        python_minor_version=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        sudo apt-get install -y python${python_minor_version}-dev || echo "⚠️  Python dev headers already installed"
        
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

# Additional audio processing
librosa>=0.10.1
scipy>=1.11.0

# Performance monitoring
psutil>=5.9.0

# Additional GPU optimizations (if GPU detected)
EOF

if [ "$gpu_detected" = true ]; then
    echo "# GPU optimizations" >> requirements_fixed.txt
    echo "accelerate>=0.24.0" >> requirements_fixed.txt
    echo "transformers>=4.35.0" >> requirements_fixed.txt
fi

# Install all dependencies
echo "📦 Installing Python packages..."
pip install -r requirements_fixed.txt

# Verify critical installations
echo "🔍 Verifying installations..."
echo "Testing core dependencies..."
python -c "import torch; print(f'✅ PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'✅ CUDA available: {torch.cuda.is_available()}')"
if [ "$gpu_detected" = true ]; then
    python -c "import torch; print(f'✅ CUDA device count: {torch.cuda.device_count()}')" || echo "⚠️  CUDA not properly configured"
fi

python -c "import deepspeech; print('✅ DeepSpeech installed')" || echo "❌ DeepSpeech installation failed"
python -c "import soundfile; print('✅ SoundFile installed')" || echo "❌ SoundFile installation failed"
python -c "import fastapi; print('✅ FastAPI installed')" || echo "❌ FastAPI installation failed"

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
echo "📍 Python executable: $(which python)"
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
Python command used: $PYTHON_CMD
Python version: $(python --version)
Python path: $(which python)
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
echo ""
echo "🚀 Ready to continue! Run the following to proceed:"
echo "   source ./activate_valper.sh"
echo "   ./scripts/setup_models.sh"

# Valper AI Environment Setup Script
# This script sets up the environment variables for the Valper AI project

echo "🚀 Setting up Valper AI Environment..."

# Create .env file if it doesn't exist
ENV_FILE="backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating .env file..."
    touch "$ENV_FILE"
else
    echo "📝 .env file already exists, updating..."
fi

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local env_var="$3"
    
    echo -n "$prompt [$default]: "
    read -r input
    
    if [ -z "$input" ]; then
        input="$default"
    fi
    
    # Update .env file
    if grep -q "^$env_var=" "$ENV_FILE"; then
        # Update existing line
        sed -i "s/^$env_var=.*/$env_var=$input/" "$ENV_FILE"
    else
        # Add new line
        echo "$env_var=$input" >> "$ENV_FILE"
    fi
}

echo ""
echo "🔧 Configuring environment variables..."

# TotalGPT API Configuration
echo ""
echo "🤖 TotalGPT API Configuration:"
echo "   Get your API key from: https://totalgpt.ai/"
prompt_with_default "Enter your TotalGPT API key" "your_api_key_here" "TOTALGPT_API_KEY"

# Backend Configuration
echo ""
echo "⚙️ Backend Configuration:"
prompt_with_default "Backend host" "0.0.0.0" "BACKEND_HOST"
prompt_with_default "Backend port" "8000" "BACKEND_PORT"
prompt_with_default "Debug mode" "True" "DEBUG"

# Audio Configuration
echo ""
echo "🎵 Audio Configuration:"
prompt_with_default "Audio sample rate" "16000" "AUDIO_SAMPLE_RATE"
prompt_with_default "Audio channels" "1" "AUDIO_CHANNELS"

# Model Configuration
echo ""
echo "🧠 Model Configuration:"
prompt_with_default "Whisper model size" "base" "WHISPER_MODEL"
prompt_with_default "TTS voice" "af_heart" "TTS_VOICE"

# Security Configuration
echo ""
echo "🔒 Security Configuration:"
prompt_with_default "CORS origins (comma-separated)" "*" "CORS_ORIGINS"
prompt_with_default "API key required" "False" "REQUIRE_API_KEY"

# Logging Configuration
echo ""
echo "📊 Logging Configuration:"
prompt_with_default "Log level" "INFO" "LOG_LEVEL"
prompt_with_default "Log file path" "logs/valper.log" "LOG_FILE"

# Create logs directory
mkdir -p logs

echo ""
echo "✅ Environment setup completed!"
echo ""
echo "📋 Configuration Summary:"
echo "   - Environment file: $ENV_FILE"
echo "   - Logs directory: logs/"
echo ""
echo "🔑 Next Steps:"
echo "   1. Make sure your TotalGPT API key is correct"
echo "   2. Start the backend: ./scripts/start_backend.sh"
echo "   3. Start the frontend: ./scripts/start_frontend.sh"
echo "   4. Access the application at: https://209.137.198.189"
echo ""
echo "⚠️  Important:"
echo "   - Keep your API keys secure and never commit them to version control"
echo "   - The .env file is already in .gitignore"
echo "   - For production, use proper SSL certificates"
echo "" 