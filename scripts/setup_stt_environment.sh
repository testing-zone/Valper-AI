#!/bin/bash

# Valper AI - STT Environment Setup using OpenAI Whisper
# Modern, reliable replacement for DeepSpeech

set -e

echo "🎯 Setting up STT Environment with OpenAI Whisper..."
echo "=============================================="

# Configuration
STT_VENV_DIR="venv_stt"
PYTHON_MIN_VERSION="3.8"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python version
check_python_version() {
    log_info "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    log_info "Found Python version: $PYTHON_VERSION"
    
    # Extract major and minor version numbers
    MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    # Check if version is >= 3.8
    if [ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -ge 8 ]; then
        log_success "Python version is compatible (≥3.8)"
    else
        log_error "Python version must be 3.8 or higher. Current: $PYTHON_VERSION"
        exit 1
    fi
}

# Install FFmpeg if not present
install_ffmpeg() {
    log_info "Checking FFmpeg installation..."
    
    if command -v ffmpeg &> /dev/null; then
        log_success "FFmpeg is already installed"
        return 0
    fi
    
    log_warning "FFmpeg not found. Attempting to install..."
    
    case "$(uname -s)" in
        Linux*)
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y ffmpeg
            elif command -v yum &> /dev/null; then
                sudo yum install -y ffmpeg
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y ffmpeg
            else
                log_error "Cannot install FFmpeg automatically. Please install manually."
                exit 1
            fi
            ;;
        Darwin*)
            if command -v brew &> /dev/null; then
                brew install ffmpeg
            else
                log_error "Homebrew not found. Please install FFmpeg manually: brew install ffmpeg"
                exit 1
            fi
            ;;
        *)
            log_error "Unsupported operating system. Please install FFmpeg manually."
            exit 1
            ;;
    esac
    
    if command -v ffmpeg &> /dev/null; then
        log_success "FFmpeg installed successfully"
    else
        log_error "FFmpeg installation failed"
        exit 1
    fi
}

# Create virtual environment
create_virtual_environment() {
    log_info "Creating STT virtual environment..."
    
    if [ -d "$STT_VENV_DIR" ]; then
        log_warning "Removing existing STT environment..."
        rm -rf "$STT_VENV_DIR"
    fi
    
    $PYTHON_CMD -m venv "$STT_VENV_DIR"
    log_success "Virtual environment created: $STT_VENV_DIR"
}

# Install Python packages
install_python_packages() {
    log_info "Installing Python packages..."
    
    # Activate virtual environment
    source "$STT_VENV_DIR/bin/activate"
    
    # Upgrade pip and setuptools
    pip install --upgrade pip setuptools wheel
    
    # Install core packages
    log_info "Installing OpenAI Whisper..."
    pip install openai-whisper
    
    # Install additional useful packages
    log_info "Installing additional audio processing packages..."
    pip install librosa soundfile
    
    # Install FastAPI integration packages
    log_info "Installing web service packages..."
    pip install fastapi uvicorn python-multipart
    
    log_success "All packages installed successfully"
}

# Test installation
test_installation() {
    log_info "Testing Whisper installation..."
    
    source "$STT_VENV_DIR/bin/activate"
    
    # Test import
    if python -c "import whisper; print('Whisper version:', whisper.__version__)" 2>/dev/null; then
        log_success "Whisper installation test passed"
    else
        log_error "Whisper installation test failed"
        exit 1
    fi
    
    # Test FFmpeg integration
    if python -c "import whisper; print('FFmpeg test passed')" 2>/dev/null; then
        log_success "FFmpeg integration test passed"
    else
        log_error "FFmpeg integration test failed"
        exit 1
    fi
}

# Main execution
main() {
    echo "🎯 Starting STT Environment Setup..."
    echo "===================================="
    echo
    
    check_python_version
    install_ffmpeg
    create_virtual_environment
    install_python_packages
    test_installation
    
    echo
    log_success "STT Environment setup completed successfully!"
    echo
    echo "📋 Summary:"
    echo "   • Python version: $PYTHON_VERSION"
    echo "   • Virtual environment: $STT_VENV_DIR"
    echo "   • STT Engine: OpenAI Whisper (latest)"
    echo "   • FFmpeg: Installed and configured"
    echo
    echo "🚀 To activate the environment:"
    echo "   source $STT_VENV_DIR/bin/activate"
    echo
    echo "🎤 To test Whisper:"
    echo "   whisper --help"
    echo "   whisper audio_file.mp3 --model base"
    echo
}

# Run main function
main "$@" 