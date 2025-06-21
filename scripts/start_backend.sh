#!/bin/bash

# Valper AI Assistant - Backend Start Script

set -e

echo "🚀 Starting Valper AI Assistant Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./scripts/setup_environment.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if models exist
if [ ! -f "models/deepspeech-0.9.3-models.pbmm" ]; then
    echo "❌ DeepSpeech models not found. Run ./scripts/setup_models.sh first"
    exit 1
fi

# Create temp directories
mkdir -p temp/audio
mkdir -p logs

# Start the backend
echo "Starting FastAPI server..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "🎉 Backend started on http://localhost:8000" 