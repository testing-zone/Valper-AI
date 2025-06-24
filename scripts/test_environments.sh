#!/bin/bash

# Valper AI - Environment Testing Script with Whisper
# Tests STT (Whisper) and TTS (Kokoro) environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_test() {
    echo -e "${PURPLE}🧪 $1${NC}"
}

log_header() {
    echo -e "${CYAN}$1${NC}"
}

# Test STT Environment (Whisper)
test_stt_environment() {
    log_header "🎤 Testing STT Environment (OpenAI Whisper)"
    echo "=============================================="
    
    if [ ! -d "venv_stt" ]; then
        log_error "STT environment not found. Run scripts/setup_stt_environment.sh first"
        return 1
    fi
    
    log_test "Activating STT environment..."
    source venv_stt/bin/activate
    
    # Test Python and pip
    log_test "Testing Python installation..."
    python_version=$(python --version 2>&1)
    pip_version=$(pip --version 2>&1)
    log_info "Python: $python_version"
    log_info "Pip: $pip_version"
    
    # Test Whisper installation
    log_test "Testing Whisper installation..."
    if python -c "import whisper; print(f'Whisper version: {whisper.__version__}')" 2>/dev/null; then
        log_success "Whisper import successful"
    else
        log_error "Whisper import failed"
        return 1
    fi
    
    # Test FFmpeg
    log_test "Testing FFmpeg integration..."
    if command -v ffmpeg &> /dev/null; then
        ffmpeg_version=$(ffmpeg -version 2>&1 | head -n 1)
        log_success "FFmpeg available: $ffmpeg_version"
    else
        log_error "FFmpeg not found"
        return 1
    fi
    
    # Test Whisper CLI
    log_test "Testing Whisper CLI..."
    if whisper --help &> /dev/null; then
        log_success "Whisper CLI working"
    else
        log_error "Whisper CLI failed"
        return 1
    fi
    
    # Test model loading
    log_test "Testing Whisper model loading (this may take a moment)..."
    if python -c "
import whisper
print('Loading tiny model for testing...')
model = whisper.load_model('tiny')
print('✅ Model loaded successfully')
print(f'Available models: {whisper.available_models()}')
" 2>/dev/null; then
        log_success "Whisper model loading successful"
    else
        log_error "Whisper model loading failed"
        return 1
    fi
    
    # Test additional packages
    log_test "Testing additional packages..."
    for package in librosa soundfile fastapi uvicorn; do
        if python -c "import $package" 2>/dev/null; then
            log_success "$package imported successfully"
        else
            log_warning "$package import failed (optional)"
        fi
    done
    
    deactivate
    log_success "STT environment tests completed successfully!"
    echo
}

# Test TTS Environment (Kokoro)
test_tts_environment() {
    log_header "🔊 Testing TTS Environment (Kokoro)"
    echo "======================================="
    
    if [ ! -d "venv_tts" ]; then
        log_error "TTS environment not found. Run scripts/setup_tts_environment.sh first"
        return 1
    fi
    
    log_test "Activating TTS environment..."
    source venv_tts/bin/activate
    
    # Test Python and pip
    log_test "Testing Python installation..."
    python_version=$(python --version 2>&1)
    pip_version=$(pip --version 2>&1)
    log_info "Python: $python_version"
    log_info "Pip: $pip_version"
    
    # Test PyTorch
    log_test "Testing PyTorch installation..."
    if python -c "import torch; print(f'PyTorch version: {torch.__version__}')" 2>/dev/null; then
        log_success "PyTorch import successful"
        
        # Test CUDA availability
        if python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>/dev/null; then
            log_info "CUDA check completed"
        fi
    else
        log_error "PyTorch import failed"
        return 1
    fi
    
    # Test Kokoro TTS components
    log_test "Testing Kokoro TTS components..."
    for package in phonemizer espeak; do
        if python -c "import $package" 2>/dev/null; then
            log_success "$package imported successfully"
        else
            log_warning "$package import failed (may need system dependencies)"
        fi
    done
    
    # Test if espeak is available system-wide
    if command -v espeak &> /dev/null; then
        log_success "espeak system command available"
    else
        log_warning "espeak system command not found"
    fi
    
    # Test additional packages
    log_test "Testing additional packages..."
    for package in numpy scipy librosa soundfile fastapi uvicorn; do
        if python -c "import $package" 2>/dev/null; then
            log_success "$package imported successfully"
        else
            log_warning "$package import failed"
        fi
    done
    
    deactivate
    log_success "TTS environment tests completed!"
    echo
}

# Test Backend Environment
test_backend_environment() {
    log_header "🖥️  Testing Backend Environment"
    echo "==============================="
    
    if [ ! -d "venv_backend" ]; then
        log_warning "Backend environment not found, creating it..."
        python3 -m venv venv_backend
        source venv_backend/bin/activate
        pip install --upgrade pip
        pip install fastapi uvicorn python-multipart
    else
        source venv_backend/bin/activate
    fi
    
    # Test FastAPI components
    log_test "Testing FastAPI components..."
    for package in fastapi uvicorn pydantic; do
        if python -c "import $package" 2>/dev/null; then
            log_success "$package imported successfully"
        else
            log_error "$package import failed"
            return 1
        fi
    done
    
    # Test backend file structure
    log_test "Testing backend file structure..."
    required_files=(
        "backend/app/main.py"
        "backend/app/services/stt_service.py"
        "backend/app/services/tts_service.py"
        "backend/app/api/routes.py"
        "backend/config.py"
    )
    
    optional_files=(
        "backend/services/stt_service.py"
        "backend/services/tts_service.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "Found: $file"
        else
            log_error "Missing: $file"
        fi
    done
    
    for file in "${optional_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "Found (optional): $file"
        fi
    done
    
    deactivate
    log_success "Backend environment tests completed!"
    echo
}

# Create a simple test audio file
create_test_audio() {
    log_test "Creating test audio file..."
    
    # Create a simple test audio using sox if available
    if command -v sox &> /dev/null; then
        sox -n -r 16000 -c 1 test_audio.wav synth 3 sine 440 vol 0.1
        log_success "Created test_audio.wav"
        return 0
    fi
    
    # Alternative: create using FFmpeg
    if command -v ffmpeg &> /dev/null; then
        ffmpeg -f lavfi -i "sine=frequency=440:duration=3" -ar 16000 -ac 1 test_audio.wav -y &>/dev/null
        log_success "Created test_audio.wav with FFmpeg"
        return 0
    fi
    
    log_warning "Cannot create test audio (sox or ffmpeg required)"
    return 1
}

# Run integration test
run_integration_test() {
    log_header "🧪 Running Integration Test"
    echo "============================"
    
    if ! create_test_audio; then
        log_warning "Skipping integration test (no test audio)"
        return 0
    fi
    
    # Test STT with Whisper
    if [ -d "venv_stt" ]; then
        log_test "Testing STT with test audio..."
        source venv_stt/bin/activate
        
        if python -c "
import whisper
model = whisper.load_model('tiny')
result = model.transcribe('test_audio.wav')
print(f'Transcription result: {result[\"text\"]}')
" 2>/dev/null; then
            log_success "STT integration test passed"
        else
            log_warning "STT integration test failed"
        fi
        
        deactivate
    fi
    
    # Clean up
    [ -f "test_audio.wav" ] && rm test_audio.wav
    echo
}

# System information
show_system_info() {
    log_header "💻 System Information"
    echo "======================"
    
    echo "OS: $(uname -s) $(uname -r)"
    echo "Architecture: $(uname -m)"
    
    if command -v lsb_release &> /dev/null; then
        echo "Distribution: $(lsb_release -d | cut -f2)"
    fi
    
    echo "Python locations:"
    for cmd in python python3 python3.8 python3.9 python3.10 python3.11; do
        if command -v $cmd &> /dev/null; then
            echo "  $cmd: $(which $cmd) ($(COLUMNS=1000 $cmd --version 2>&1))"
        fi
    done
    
    echo "Memory: $(free -h 2>/dev/null | grep Mem || echo 'N/A')"
    echo "Disk space: $(df -h . | tail -1 | awk '{print $4 " available"}')"
    
    # GPU information
    if command -v nvidia-smi &> /dev/null; then
        echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)"
    else
        echo "GPU: No NVIDIA GPU detected"
    fi
    
    echo
}

# Troubleshooting guide
show_troubleshooting() {
    log_header "🔧 Troubleshooting Guide"
    echo "========================="
    
    echo "Common issues and solutions:"
    echo
    echo "1. FFmpeg not found:"
    echo "   Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "   macOS: brew install ffmpeg"
    echo "   Windows: Use chocolatey or download from ffmpeg.org"
    echo
    echo "2. Python version issues:"
    echo "   Ensure Python 3.8+ is installed"
    echo "   Use pyenv to manage multiple Python versions"
    echo
    echo "3. Whisper model download issues:"
    echo "   Check internet connection"
    echo "   Try smaller model first: whisper --model tiny"
    echo
    echo "4. Memory issues:"
    echo "   Use smaller Whisper models (tiny, base)"
    echo "   Close other applications"
    echo
    echo "5. Permission issues:"
    echo "   Check file permissions on virtual environments"
    echo "   Ensure user has write access to project directory"
    echo
    echo "For more help, check the project documentation or GitHub issues."
    echo
}

# Main function
main() {
    echo "🧪 Valper AI Environment Testing Suite"
    echo "======================================"
    echo
    
    show_system_info
    
    # Test environments
    test_stt_environment
    test_tts_environment
    test_backend_environment
    
    # Run integration test
    run_integration_test
    
    echo "🎉 Testing completed!"
    echo
    echo "Next steps:"
    echo "  • If all tests passed: run scripts/start_backend.sh"
    echo "  • If tests failed: check troubleshooting guide below"
    echo
    
    show_troubleshooting
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stt-only)
            test_stt_environment
            exit 0
            ;;
        --tts-only)
            test_tts_environment
            exit 0
            ;;
        --backend-only)
            test_backend_environment
            exit 0
            ;;
        --integration-only)
            run_integration_test
            exit 0
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --stt-only         Test only STT environment"
            echo "  --tts-only         Test only TTS environment"
            echo "  --backend-only     Test only backend environment"
            echo "  --integration-only Run only integration tests"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
    shift
done

# Run main function if no specific options provided
main 