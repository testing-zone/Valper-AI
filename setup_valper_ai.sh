#!/bin/bash

# Valper AI Assistant - Master Setup Script
# This script orchestrates the complete setup process for Valper AI

set -e

echo "🤖 Valper AI Assistant - Complete Setup"
echo "======================================="
echo "This script will set up your complete voice assistant with:"
echo "🎤 STT: DeepSpeech (Python 3.8-3.10)"
echo "🔊 TTS: Kokoro (Python 3.9+)"
echo "🚀 Backend: FastAPI with dual environment support"
echo "🌐 Frontend: React with modern UI"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📍 Step $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to confirm continuation
confirm_step() {
    echo ""
    read -p "Press Enter to continue, or Ctrl+C to exit..."
    echo ""
}

# Main setup process
main() {
    print_step "1" "Pre-setup verification"
    echo "Checking system requirements and project structure..."
    
    # Check if we're in the right directory
    if [ ! -f "backend/app/main.py" ]; then
        print_error "Please run this script from the Valper-AI root directory"
        exit 1
    fi
    
    # Check for required tools
    for tool in wget curl git python3; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    print_success "System requirements check passed"
    confirm_step
    
    # Step 2: Clean setup
    print_step "2" "Clean environment setup"
    echo "Removing any existing environments and starting fresh..."
    
    if [ -f "scripts/cleanup_and_setup.sh" ]; then
        chmod +x scripts/cleanup_and_setup.sh
        ./scripts/cleanup_and_setup.sh
    else
        print_error "Cleanup script not found!"
        exit 1
    fi
    
    print_success "Environment setup completed"
    confirm_step
    
    # Step 3: Test environments
    print_step "3" "Environment testing and validation"
    echo "Testing that both STT and TTS environments work correctly..."
    
    if [ -f "scripts/test_environments.sh" ]; then
        chmod +x scripts/test_environments.sh
        ./scripts/test_environments.sh
    else
        print_warning "Test script not found, skipping tests"
    fi
    
    print_success "Environment testing completed"
    confirm_step
    
    # Step 4: Start backend
    print_step "4" "Backend server startup"
    echo "Starting the backend server..."
    echo "This will run in the background so you can continue with frontend setup."
    
    if [ -f "scripts/start_backend.sh" ]; then
        chmod +x scripts/start_backend.sh
        
        echo "Starting backend in background..."
        nohup ./scripts/start_backend.sh > logs/backend.log 2>&1 &
        backend_pid=$!
        echo $backend_pid > logs/backend.pid
        
        # Wait for backend to start
        echo "Waiting for backend to start..."
        sleep 10
        
        # Check if backend is running
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is running on http://localhost:8000"
        else
            print_warning "Backend may not be fully ready yet (check logs/backend.log)"
        fi
    else
        print_error "Backend start script not found!"
        exit 1
    fi
    
    confirm_step
    
    # Step 5: Setup frontend
    print_step "5" "Frontend setup and startup"
    echo "Setting up and starting the React frontend..."
    
    if [ -f "scripts/start_frontend.sh" ]; then
        chmod +x scripts/start_frontend.sh
        
        echo "Installing frontend dependencies..."
        cd frontend
        if command -v npm &> /dev/null; then
            npm install
        elif command -v yarn &> /dev/null; then
            yarn install
        else
            print_error "npm or yarn is required for frontend setup"
            echo "Install Node.js and npm: https://nodejs.org/"
            exit 1
        fi
        cd ..
        
        print_success "Frontend dependencies installed"
        
        echo "Frontend will be started in a new terminal window."
        echo "If it doesn't open automatically, run: ./scripts/start_frontend.sh"
        
        # Try to open frontend in new terminal
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "./scripts/start_frontend.sh; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -e "./scripts/start_frontend.sh" &
        else
            echo "Please open a new terminal and run: ./scripts/start_frontend.sh"
        fi
        
    else
        print_warning "Frontend start script not found, manual setup required"
    fi
    
    # Step 6: Final instructions
    print_step "6" "Setup completion and next steps"
    echo ""
    echo "🎉 Valper AI Assistant Setup Complete!"
    echo "======================================"
    echo ""
    echo "🌐 Access your voice assistant:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo ""
    echo "🔧 Environment Details:"
    echo "   STT (DeepSpeech): venv_stt/"
    echo "   TTS (Kokoro): venv_tts/"
    echo "   Backend: venv_backend/"
    echo ""
    echo "📝 Log Files:"
    echo "   Backend: logs/backend.log"
    echo "   Test Results: logs/test_results.txt"
    echo ""
    echo "🎤 Usage Instructions:"
    echo "1. Open http://localhost:3000 in your browser"
    echo "2. Click the microphone button to start recording"
    echo "3. Speak your message"
    echo "4. The assistant will transcribe and respond with speech"
    echo ""
    echo "🔧 Management Commands:"
    echo "   Stop backend: kill \$(cat logs/backend.pid)"
    echo "   Restart backend: ./scripts/start_backend.sh"
    echo "   Test environments: ./scripts/test_environments.sh"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   If issues occur, check logs/ directory for error details"
    echo "   Run ./scripts/test_environments.sh for diagnostics"
    echo ""
    print_success "Your Valper AI Assistant is ready! 🚀"
}

# Create logs directory
mkdir -p logs

# Run main setup
main "$@"

echo ""
echo "Setup script completed. Enjoy your AI assistant!" 