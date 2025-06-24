#!/bin/bash

# Valper AI - Master Setup Script
# Sets up complete voice assistant with OpenAI Whisper (STT) and Kokoro TTS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="Valper AI"
VERSION="2.0.0"
STT_ENGINE="OpenAI Whisper"
TTS_ENGINE="Kokoro TTS"

# Functions for colored output
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

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

log_header() {
    echo -e "${CYAN}$1${NC}"
}

# Header
show_header() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║                       🎤 VALPER AI 🤖                         ║"
    echo "║                                                               ║"
    echo "║           Your Advanced Voice Assistant Setup v2.0           ║"
    echo "║                                                               ║"
    echo "║  🎯 OpenAI Whisper (STT) + Kokoro TTS + FastAPI + React     ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

# System requirements check
check_system_requirements() {
    log_header "📋 Checking System Requirements"
    echo "================================"
    
    # Check OS
    OS=$(uname -s)
    log_info "Operating System: $OS"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        log_success "Python 3 found: $PYTHON_VERSION"
        
        # Check if version is >= 3.8
        MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -ge 8 ]; then
            log_success "Python version is compatible (≥3.8)"
        else
            log_error "Python 3.8+ required. Current: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        log_success "Git found: $(git --version)"
    else
        log_warning "Git not found (recommended for development)"
    fi
    
    # Check Node.js (for frontend)
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js found: $NODE_VERSION"
    else
        log_warning "Node.js not found (required for frontend)"
        echo "Install from: https://nodejs.org/"
    fi
    
    # Check available disk space
    AVAILABLE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
    log_info "Available disk space: $AVAILABLE_SPACE"
    
    echo
}

# Confirmation prompt
get_user_confirmation() {
    log_header "🚀 Ready to Setup Valper AI"
    echo "============================="
    echo
    echo "This will install:"
    echo "  • 🎤 OpenAI Whisper (Speech-to-Text)"
    echo "  • 🔊 Kokoro TTS (Text-to-Speech)"
    echo "  • 🖥️  FastAPI Backend"
    echo "  • 🌐 React Frontend"
    echo "  • 🐳 Docker Configuration"
    echo
    echo "Estimated installation time: 10-15 minutes"
    echo "Required disk space: ~2-3 GB"
    echo
    
    while true; do
        read -p "Continue with installation? (y/n): " yn
        case $yn in
            [Yy]* ) 
                log_success "Starting installation..."
                break
                ;;
            [Nn]* ) 
                log_info "Installation cancelled by user"
                exit 0
                ;;
            * ) 
                echo "Please answer yes (y) or no (n)"
                ;;
        esac
    done
    echo
}

# Step 1: Environment Setup
setup_environments() {
    log_header "🏗️  Step 1: Setting up Environments"
    echo "==================================="
    
    log_step "Setting up STT environment with OpenAI Whisper..."
    if [ -f "scripts/setup_stt_environment.sh" ]; then
        chmod +x scripts/setup_stt_environment.sh
        ./scripts/setup_stt_environment.sh
        log_success "STT environment setup completed"
    else
        log_error "STT setup script not found"
        exit 1
    fi
    
    echo
    log_step "Setting up TTS environment with Kokoro..."
    if [ -f "scripts/setup_tts_environment.sh" ]; then
        chmod +x scripts/setup_tts_environment.sh
        ./scripts/setup_tts_environment.sh
        log_success "TTS environment setup completed"
    else
        log_error "TTS setup script not found"
        exit 1
    fi
    
    echo
}

# Step 2: Testing
run_tests() {
    log_header "🧪 Step 2: Testing Environments"
    echo "==============================="
    
    log_step "Running comprehensive environment tests..."
    if [ -f "scripts/test_environments.sh" ]; then
        chmod +x scripts/test_environments.sh
        ./scripts/test_environments.sh
        log_success "Environment tests completed"
    else
        log_error "Test script not found"
        exit 1
    fi
    
    echo
}

# Step 3: Backend Setup
setup_backend() {
    log_header "🖥️  Step 3: Setting up Backend"
    echo "============================="
    
    log_step "Creating backend environment..."
    if [ ! -d "venv_backend" ]; then
        python3 -m venv venv_backend
        source venv_backend/bin/activate
        pip install --upgrade pip
        
        # Install backend dependencies
        log_step "Installing backend dependencies..."
        pip install fastapi uvicorn python-multipart
        
        # Install additional dependencies if requirements.txt exists
        if [ -f "backend/requirements.txt" ]; then
            pip install -r backend/requirements.txt
        fi
        
        deactivate
        log_success "Backend environment created"
    else
        log_success "Backend environment already exists"
    fi
    
    echo
}

# Step 4: Frontend Setup
setup_frontend() {
    log_header "🌐 Step 4: Setting up Frontend"
    echo "=============================="
    
    if command -v npm &> /dev/null; then
        log_step "Installing frontend dependencies..."
        cd frontend
        
        if [ -f "package.json" ]; then
            npm install
            log_success "Frontend dependencies installed"
        else
            log_warning "Frontend package.json not found"
        fi
        
        cd ..
    else
        log_warning "npm not found. Skipping frontend setup."
        log_info "Install Node.js from https://nodejs.org/ to setup frontend"
    fi
    
    echo
}

# Step 5: Configuration
setup_configuration() {
    log_header "⚙️  Step 5: Configuration"
    echo "========================"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_step "Creating environment configuration..."
        cat > .env << EOF
# Valper AI Configuration
PROJECT_NAME=Valper AI
VERSION=2.0.0

# STT Configuration (OpenAI Whisper)
STT_ENGINE=whisper
WHISPER_MODEL=base

# TTS Configuration (Kokoro)
TTS_ENGINE=kokoro
TTS_VOICE=default

# API Configuration
API_HOST=localhost
API_PORT=8000

# Frontend Configuration
FRONTEND_PORT=3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/valper.log

# Performance
MAX_AUDIO_DURATION=300
MAX_TEXT_LENGTH=1000
EOF
        log_success "Configuration file created: .env"
    else
        log_success "Configuration file already exists: .env"
    fi
    
    # Create logs directory
    mkdir -p logs
    log_success "Logs directory created"
    
    echo
}

# Step 6: Docker Setup (Optional)
setup_docker() {
    log_header "🐳 Step 6: Docker Setup (Optional)"
    echo "=================================="
    
    if command -v docker &> /dev/null; then
        log_success "Docker found: $(docker --version)"
        
        if [ -f "docker-compose.yml" ]; then
            log_step "Docker configuration ready"
            echo "  • To build: docker-compose build"
            echo "  • To run: docker-compose up"
        else
            log_warning "docker-compose.yml not found"
        fi
    else
        log_warning "Docker not found"
        log_info "Install Docker from https://docker.com/ for containerized deployment"
    fi
    
    echo
}

# Step 7: Final verification
final_verification() {
    log_header "✅ Final Verification"
    echo "====================="
    
    log_step "Checking installation..."
    
    # Check environments
    if [ -d "venv_stt" ]; then
        log_success "STT environment ready"
    else
        log_error "STT environment missing"
    fi
    
    if [ -d "venv_tts" ]; then
        log_success "TTS environment ready"
    else
        log_error "TTS environment missing"
    fi
    
    if [ -d "venv_backend" ]; then
        log_success "Backend environment ready"
    else
        log_warning "Backend environment missing"
    fi
    
    # Check key files
    key_files=(
        "backend/main.py"
        "backend/services/stt_service.py"
        "backend/services/tts_service.py"
        "frontend/package.json"
        ".env"
    )
    
    for file in "${key_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "Found: $file"
        else
            log_warning "Missing: $file"
        fi
    done
    
    echo
}

# Success message and next steps
show_success() {
    log_header "🎉 Installation Complete!"
    echo "=========================="
    echo
    echo "🎤 Valper AI is now ready to use!"
    echo
    echo "📋 What was installed:"
    echo "  ✅ OpenAI Whisper (Speech-to-Text)"
    echo "  ✅ Kokoro TTS (Text-to-Speech)"
    echo "  ✅ FastAPI Backend"
    echo "  ✅ React Frontend"
    echo "  ✅ Environment Configuration"
    echo
    echo "🚀 Quick Start:"
    echo "  1. Start Backend:"
    echo "     ./scripts/start_backend.sh"
    echo
    echo "  2. Start Frontend (in new terminal):"
    echo "     ./scripts/start_frontend.sh"
    echo
    echo "  3. Open your browser:"
    echo "     http://localhost:3000"
    echo
    echo "🔧 Useful Commands:"
    echo "  • Test environments: ./scripts/test_environments.sh"
    echo "  • View logs: tail -f logs/valper.log"
    echo "  • Update models: ./scripts/setup_models.sh"
    echo
    echo "📚 Documentation:"
    echo "  • API docs: http://localhost:8000/docs"
    echo "  • Project README: ./README.md"
    echo
    echo "🎯 Enjoy your new AI voice assistant!"
    echo
}

# Error handling
handle_error() {
    local exit_code=$?
    log_error "Setup failed with exit code: $exit_code"
    echo
    echo "🔧 Troubleshooting:"
    echo "  • Check logs: tail -f logs/setup.log"
    echo "  • Run tests: ./scripts/test_environments.sh"
    echo "  • Clean restart: rm -rf venv_* && ./setup_valper_ai.sh"
    echo
    exit $exit_code
}

# Set up error handling
trap handle_error ERR

# Create logs directory and setup logging
mkdir -p logs
exec 1> >(tee -a logs/setup.log)
exec 2> >(tee -a logs/setup.log >&2)

# Main execution
main() {
    show_header
    check_system_requirements
    get_user_confirmation
    
    log_info "Starting Valper AI setup at $(date)"
    echo
    
    setup_environments
    run_tests
    setup_backend
    setup_frontend
    setup_configuration
    setup_docker
    final_verification
    
    show_success
    
    log_info "Setup completed successfully at $(date)"
}

# Execute main function
main "$@" 