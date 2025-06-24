#!/bin/bash

# Valper AI Assistant - Environment Testing Script
# This script tests both STT and TTS environments and provides troubleshooting

set -e

echo "🧪 Valper AI - Environment Testing & Troubleshooting"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    case $1 in
        "ERROR") echo -e "${RED}❌ $2${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ $2${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  $2${NC}" ;;
        "INFO") echo -e "${BLUE}ℹ️  $2${NC}" ;;
    esac
}

# Function to test STT environment
test_stt_environment() {
    echo ""
    echo "🎤 Testing STT (DeepSpeech) Environment"
    echo "======================================"
    
    # Check if STT environment exists
    if [ ! -d "venv_stt" ]; then
        print_status "ERROR" "STT environment not found"
        echo "Run: ./scripts/setup_stt_environment.sh"
        return 1
    fi
    
    print_status "SUCCESS" "STT environment directory found"
    
    # Test STT environment activation
    echo "🔄 Testing STT environment activation..."
    if source venv_stt/bin/activate; then
        print_status "SUCCESS" "STT environment activated"
        
        # Test Python version
        python_version=$(python --version 2>&1)
        print_status "INFO" "Python version: $python_version"
        
        # Test DeepSpeech import
        echo "📦 Testing DeepSpeech import..."
        if python -c "import deepspeech; print(f'DeepSpeech version: {deepspeech.__version__}')" 2>/dev/null; then
            print_status "SUCCESS" "DeepSpeech imported successfully"
        else
            print_status "ERROR" "DeepSpeech import failed"
            echo "Troubleshooting:"
            echo "1. Check if DeepSpeech was installed: pip list | grep deepspeech"
            echo "2. Try reinstalling: pip install deepspeech==0.9.3"
            echo "3. Check Python version compatibility (3.8-3.10 required)"
        fi
        
        # Test audio dependencies
        echo "🔊 Testing audio dependencies..."
        deps_ok=true
        
        for dep in numpy soundfile librosa; do
            if python -c "import $dep" 2>/dev/null; then
                print_status "SUCCESS" "$dep imported successfully"
            else
                print_status "ERROR" "$dep import failed"
                deps_ok=false
            fi
        done
        
        # Test model files
        echo "📁 Testing model files..."
        if [ -f "models/stt/deepspeech-0.9.3-models.pbmm" ]; then
            print_status "SUCCESS" "DeepSpeech model file found"
        else
            print_status "ERROR" "DeepSpeech model file not found"
            echo "Download with: wget -O models/stt/deepspeech-0.9.3-models.pbmm https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm"
        fi
        
        if [ -f "models/stt/deepspeech-0.9.3-models.scorer" ]; then
            print_status "SUCCESS" "DeepSpeech scorer file found"
        else
            print_status "WARNING" "DeepSpeech scorer file not found (optional)"
        fi
        
        # Test STT functionality
        echo "🎯 Testing STT functionality..."
        cat > test_stt.py << 'EOF'
import sys
import os
sys.path.append('backend')

try:
    from app.services.stt_service import STTService
    import asyncio
    
    async def test_stt():
        stt = STTService()
        await stt.initialize()
        
        if stt.is_available():
            print("✅ STT service initialized successfully")
            info = stt.get_info()
            print(f"✅ STT info: {info}")
            return True
        else:
            print("❌ STT service initialization failed")
            return False
    
    result = asyncio.run(test_stt())
    if result:
        print("✅ STT functionality test PASSED")
    else:
        print("❌ STT functionality test FAILED")
        
except Exception as e:
    print(f"❌ STT test error: {e}")
EOF
        
        if python test_stt.py; then
            print_status "SUCCESS" "STT functionality test completed"
        else
            print_status "ERROR" "STT functionality test failed"
        fi
        
        rm -f test_stt.py
        deactivate
        
    else
        print_status "ERROR" "Failed to activate STT environment"
        return 1
    fi
}

# Function to test TTS environment
test_tts_environment() {
    echo ""
    echo "🔊 Testing TTS (Kokoro) Environment"
    echo "==================================="
    
    # Check if TTS environment exists
    if [ ! -d "venv_tts" ]; then
        print_status "ERROR" "TTS environment not found"
        echo "Run: ./scripts/setup_tts_environment.sh"
        return 1
    fi
    
    print_status "SUCCESS" "TTS environment directory found"
    
    # Test TTS environment activation
    echo "🔄 Testing TTS environment activation..."
    if source venv_tts/bin/activate; then
        print_status "SUCCESS" "TTS environment activated"
        
        # Test Python version
        python_version=$(python --version 2>&1)
        print_status "INFO" "Python version: $python_version"
        
        # Test PyTorch
        echo "🔥 Testing PyTorch..."
        if python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')" 2>/dev/null; then
            print_status "SUCCESS" "PyTorch imported successfully"
        else
            print_status "ERROR" "PyTorch import failed"
            echo "Troubleshooting:"
            echo "1. Reinstall PyTorch: pip install torch torchaudio"
            echo "2. For GPU: pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118"
        fi
        
        # Test Kokoro TTS
        echo "🎵 Testing Kokoro TTS..."
        if python -c "from kokoro import KPipeline; print('Kokoro TTS imported successfully')" 2>/dev/null; then
            print_status "SUCCESS" "Kokoro TTS imported successfully"
        else
            print_status "WARNING" "Kokoro TTS import failed, checking fallback..."
            if python -c "import pyttsx3; print('Fallback TTS (pyttsx3) available')" 2>/dev/null; then
                print_status "SUCCESS" "Fallback TTS available"
            else
                print_status "ERROR" "No TTS available"
                echo "Install fallback: pip install pyttsx3"
            fi
        fi
        
        # Test audio dependencies
        echo "🔊 Testing audio dependencies..."
        for dep in numpy soundfile librosa scipy; do
            if python -c "import $dep" 2>/dev/null; then
                print_status "SUCCESS" "$dep imported successfully"
            else
                print_status "ERROR" "$dep import failed"
            fi
        done
        
        # Test TTS functionality
        echo "🎯 Testing TTS functionality..."
        cat > test_tts.py << 'EOF'
import sys
import os
sys.path.append('backend')

try:
    from app.services.tts_service import TTSService
    import asyncio
    
    async def test_tts():
        tts = TTSService()
        await tts.initialize()
        
        if tts.is_available():
            print("✅ TTS service initialized successfully")
            info = tts.get_info()
            print(f"✅ TTS info: {info}")
            
            # Test basic synthesis
            print("🎵 Testing speech synthesis...")
            audio_file = await tts.synthesize_speech("Hello, this is a test of the TTS system.")
            if audio_file:
                print(f"✅ Audio generated: {audio_file}")
                # Clean up test file
                if os.path.exists(audio_file):
                    os.unlink(audio_file)
                return True
            else:
                print("❌ Audio generation failed")
                return False
        else:
            print("❌ TTS service initialization failed")
            return False
    
    result = asyncio.run(test_tts())
    if result:
        print("✅ TTS functionality test PASSED")
    else:
        print("❌ TTS functionality test FAILED")
        
except Exception as e:
    print(f"❌ TTS test error: {e}")
EOF
        
        if python test_tts.py; then
            print_status "SUCCESS" "TTS functionality test completed"
        else
            print_status "ERROR" "TTS functionality test failed"
        fi
        
        rm -f test_tts.py
        deactivate
        
    else
        print_status "ERROR" "Failed to activate TTS environment"
        return 1
    fi
}

# Function to test backend integration
test_backend_integration() {
    echo ""
    echo "🔗 Testing Backend Integration"
    echo "============================="
    
    # Check if backend files exist
    if [ ! -f "backend/app/main.py" ]; then
        print_status "ERROR" "Backend main.py not found"
        return 1
    fi
    
    print_status "SUCCESS" "Backend files found"
    
    # Test FastAPI dependencies
    echo "🚀 Testing FastAPI dependencies..."
    # Use the main venv or create a temporary one for backend testing
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_tts" ]; then
        source venv_tts/bin/activate
    else
        print_status "ERROR" "No Python environment found for backend testing"
        return 1
    fi
    
    for dep in fastapi uvicorn pydantic python-multipart; do
        if python -c "import ${dep/_/-}" 2>/dev/null; then
            print_status "SUCCESS" "$dep available"
        else
            print_status "WARNING" "$dep not found in current environment"
        fi
    done
    
    # Test backend import
    echo "📦 Testing backend imports..."
    if python -c "
import sys
sys.path.append('backend')
try:
    from app.main import app
    print('✅ Backend app imported successfully')
except Exception as e:
    print(f'❌ Backend import failed: {e}')
" 2>/dev/null; then
        print_status "SUCCESS" "Backend imports successful"
    else
        print_status "ERROR" "Backend import failed"
    fi
    
    deactivate 2>/dev/null || true
}

# Function to run API tests
test_api_endpoints() {
    echo ""
    echo "🌐 Testing API Endpoints"
    echo "======================="
    
    echo "📝 This test requires the backend to be running"
    echo "To start backend: ./scripts/start_backend.sh"
    echo ""
    
    # Check if backend is running
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "SUCCESS" "Backend is running"
        
        # Test health endpoint
        echo "🔍 Testing /health endpoint..."
        response=$(curl -s http://localhost:8000/health)
        if echo "$response" | grep -q "status"; then
            print_status "SUCCESS" "Health endpoint working"
        else
            print_status "ERROR" "Health endpoint failed"
        fi
        
        # Test STT info endpoint
        echo "🎤 Testing /api/v1/stt/info endpoint..."
        if curl -s http://localhost:8000/api/v1/stt/info > /dev/null; then
            print_status "SUCCESS" "STT info endpoint accessible"
        else
            print_status "WARNING" "STT info endpoint not accessible"
        fi
        
        # Test TTS info endpoint
        echo "🔊 Testing /api/v1/tts/info endpoint..."
        if curl -s http://localhost:8000/api/v1/tts/info > /dev/null; then
            print_status "SUCCESS" "TTS info endpoint accessible"
        else
            print_status "WARNING" "TTS info endpoint not accessible"
        fi
        
    else
        print_status "WARNING" "Backend is not running"
        echo "Start backend with: ./scripts/start_backend.sh"
        echo "Then run this test again to verify API endpoints"
    fi
}

# Function to provide troubleshooting tips
provide_troubleshooting() {
    echo ""
    echo "🔧 Troubleshooting Guide"
    echo "======================"
    
    echo "Common Issues and Solutions:"
    echo ""
    
    echo "1. 📦 Package Import Errors:"
    echo "   - Ensure you're in the correct virtual environment"
    echo "   - Reinstall packages: pip install -r requirements.txt"
    echo "   - Check Python version compatibility"
    echo ""
    
    echo "2. 🎤 DeepSpeech Issues:"
    echo "   - Python 3.8-3.10 required (not 3.11+)"
    echo "   - Download models manually if wget failed"
    echo "   - Check system dependencies: sudo apt install sox libsox-dev"
    echo ""
    
    echo "3. 🔊 Kokoro TTS Issues:"
    echo "   - Python 3.9+ required"
    echo "   - GPU drivers needed for CUDA support"
    echo "   - Fallback to pyttsx3 if Kokoro fails"
    echo ""
    
    echo "4. 🌐 API Issues:"
    echo "   - Check if backend is running: curl http://localhost:8000/health"
    echo "   - Verify port 8000 is not in use: lsof -i :8000"
    echo "   - Check backend logs for errors"
    echo ""
    
    echo "5. 🔄 Environment Issues:"
    echo "   - Clean restart: rm -rf venv_* && ./scripts/cleanup_and_setup.sh"
    echo "   - Check system dependencies: ./scripts/install_system_deps.sh"
    echo "   - Verify permissions on directories"
    echo ""
}

# Main execution
main() {
    echo "Starting comprehensive environment testing..."
    echo ""
    
    # Initialize counters
    total_tests=0
    passed_tests=0
    
    # Test STT environment
    if test_stt_environment; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Test TTS environment
    if test_tts_environment; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Test backend integration
    if test_backend_integration; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Test API endpoints
    test_api_endpoints
    ((total_tests++))
    
    # Final results
    echo ""
    echo "🎯 Test Results Summary"
    echo "====================="
    echo "Tests passed: $passed_tests/$total_tests"
    
    if [ $passed_tests -eq $total_tests ]; then
        print_status "SUCCESS" "All core tests passed! 🎉"
        echo ""
        echo "🚀 Ready to start your voice assistant!"
        echo "Next steps:"
        echo "1. Start backend: ./scripts/start_backend.sh"
        echo "2. Start frontend: ./scripts/start_frontend.sh"
        echo "3. Open http://localhost:3000 in your browser"
    else
        print_status "WARNING" "Some tests failed. Check the troubleshooting guide below."
        provide_troubleshooting
    fi
    
    echo ""
    echo "📝 Environment info saved to: logs/test_results.txt"
    
    # Save test results
    mkdir -p logs
    {
        echo "Valper AI Environment Test Results"
        echo "================================="
        echo "Date: $(date)"
        echo "Tests passed: $passed_tests/$total_tests"
        echo ""
        echo "Environment details:"
        echo "- STT Environment: $([ -d venv_stt ] && echo "Present" || echo "Missing")"
        echo "- TTS Environment: $([ -d venv_tts ] && echo "Present" || echo "Missing")"
        echo "- Backend: $([ -f backend/app/main.py ] && echo "Present" || echo "Missing")"
        echo "- System: $(uname -a)"
    } > logs/test_results.txt
}

# Run main function
main "$@" 