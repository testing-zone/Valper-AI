#!/bin/bash

# Valper AI Assistant - Backend Start Script
# This script starts the backend with proper environment handling

set -e

echo "🚀 Starting Valper AI Backend..."

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Please run this script from the Valper-AI root directory"
    exit 1
fi

# Function to check environments
check_environments() {
    echo "🔍 Checking environments..."
    
    if [ ! -d "venv_stt" ]; then
        echo "❌ STT environment not found. Run: ./scripts/setup_stt_environment.sh"
        return 1
    fi
    
    if [ ! -d "venv_tts" ]; then
        echo "❌ TTS environment not found. Run: ./scripts/setup_tts_environment.sh"
        return 1
    fi
    
    echo "✅ Both STT and TTS environments found"
    return 0
}

# Create a backend environment with necessary dependencies
setup_backend_env() {
    echo "🏗️  Setting up backend environment..."
    
    # Use TTS environment as base (it has more modern dependencies)
    if [ ! -d "venv_backend" ]; then
        echo "📦 Creating backend environment based on TTS environment..."
        cp -r venv_tts venv_backend
    fi
    
    # Activate backend environment
    source venv_backend/bin/activate
    
    # Install FastAPI and backend dependencies
    echo "📦 Installing backend dependencies..."
    pip install \
        fastapi==0.104.1 \
        uvicorn[standard]==0.24.0 \
        python-multipart==0.0.6 \
        websockets==12.0 \
        pydantic==2.5.0 \
        python-jose[cryptography]==3.3.0 \
        passlib[bcrypt]==1.7.4 \
        python-dotenv==1.0.0 \
        aiofiles==23.2.1 \
        httpx==0.25.2 \
        soundfile==0.12.1
    
    # Test backend imports
    echo "🔍 Testing backend imports..."
    python -c "
import sys
sys.path.append('backend')
from app.main import app
print('✅ Backend imports successful')
"
    
    deactivate
}

# Start the backend server
start_server() {
    echo "🚀 Starting FastAPI server..."
    
    # Activate backend environment
    source venv_backend/bin/activate
    
    # Set environment variables
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
    export STT_ENV_PATH="$(pwd)/venv_stt"
    export TTS_ENV_PATH="$(pwd)/venv_tts"
    
    # Create necessary directories
    mkdir -p temp/audio logs
    
    # Start the server
    echo "📍 Backend starting on http://localhost:8000"
    echo "📍 API documentation: http://localhost:8000/docs"
    echo "📍 Press Ctrl+C to stop"
    echo ""
    
    cd backend
    
    # Start with hot reload for development
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level info \
        --access-log
}

# Main execution
main() {
    echo "Starting Valper AI backend server..."
    echo ""
    
    # Check environments
    if ! check_environments; then
        echo ""
        echo "🔧 Fix environments first:"
        echo "1. Run: ./scripts/cleanup_and_setup.sh"
        echo "2. Then run this script again"
        exit 1
    fi
    
    # Setup backend environment
    setup_backend_env
    
    # Start server
    start_server
}

# Handle script interruption
trap 'echo -e "\n🛑 Backend server stopped"; exit 0' INT

# Run main function
main "$@" 