#!/bin/bash

# Valper AI Assistant - Environment Activation Script
# This script activates the isolated Python environment for Valper AI

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Activating Valper AI environment...${NC}"

# Check if we're in the right directory
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run this script from the Valper AI project root directory.${NC}"
    echo -e "${YELLOW}Or run './scripts/setup_environment.sh' to create the environment.${NC}"
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

# Verify activation
if [ "$VIRTUAL_ENV" != "" ]; then
    echo -e "${GREEN}✅ Environment activated successfully!${NC}"
else
    echo -e "${RED}❌ Failed to activate environment${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📍 Environment Info:${NC}"
echo -e "  Python: ${GREEN}$(which python)${NC}"
echo -e "  Python version: ${GREEN}$(python --version)${NC}"
echo -e "  Virtual env: ${GREEN}$VIRTUAL_ENV${NC}"
echo -e "  Working directory: ${GREEN}$(pwd)${NC}"

# Check GPU status
echo ""
echo -e "${BLUE}🎮 GPU Status:${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}NVIDIA GPU detected${NC}"
    python -c "
import torch
print(f'  PyTorch CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  CUDA devices: {torch.cuda.device_count()}')
    print(f'  Current device: {torch.cuda.get_device_name(0)}')
    print(f'  CUDA version: {torch.version.cuda}')
else:
    print('  Using CPU mode')
" 2>/dev/null || echo -e "${YELLOW}  PyTorch not installed yet${NC}"
else
    echo -e "${YELLOW}No NVIDIA GPU detected (CPU mode)${NC}"
fi

echo ""
echo -e "${BLUE}🛠️  Available Commands:${NC}"
echo -e "  ${GREEN}./scripts/setup_models.sh${NC}    - Download AI models"
echo -e "  ${GREEN}./scripts/start_backend.sh${NC}   - Start backend server"
echo -e "  ${GREEN}./scripts/start_frontend.sh${NC}  - Start frontend (in another terminal)"
echo -e "  ${GREEN}deactivate${NC}                   - Exit this environment"

echo ""
echo -e "${BLUE}📊 Quick Status Check:${NC}"
if [ -f "models/deepspeech-0.9.3-models.pbmm" ]; then
    echo -e "  Models: ${GREEN}Downloaded ✅${NC}"
else
    echo -e "  Models: ${YELLOW}Not downloaded (run ./scripts/setup_models.sh)${NC}"
fi

if [ -d "frontend/node_modules" ]; then
    echo -e "  Frontend deps: ${GREEN}Installed ✅${NC}"
else
    echo -e "  Frontend deps: ${YELLOW}Not installed (run ./scripts/start_frontend.sh)${NC}"
fi

# Check if ports are in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "  Backend: ${GREEN}Running on port 8000 ✅${NC}"
else
    echo -e "  Backend: ${YELLOW}Not running${NC}"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "  Frontend: ${GREEN}Running on port 3000 ✅${NC}"
else
    echo -e "  Frontend: ${YELLOW}Not running${NC}"
fi

echo ""
echo -e "${GREEN}💡 Environment is ready! No conflicts with other Python projects.${NC}"
echo -e "${BLUE}🌐 When running: Frontend → http://localhost:3000, API → http://localhost:8000/docs${NC}" 