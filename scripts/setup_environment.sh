#!/bin/bash

# Valper AI Assistant - Environment Setup Script
# This script sets up the Python environment and installs dependencies

set -e

echo "🐍 Setting up Valper AI Assistant environment..."

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required, found Python $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install system dependencies for audio processing
echo "Installing system dependencies..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install portaudio
        brew install espeak-ng
    else
        echo "⚠️  Please install Homebrew and run: brew install portaudio espeak-ng"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev espeak-ng
fi

# Install Python dependencies
echo "Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Create necessary directories
echo "Creating directories..."
mkdir -p models
mkdir -p temp/audio
mkdir -p logs

echo "🎉 Environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "Next steps:"
echo "  1. Run './scripts/setup_models.sh' to download AI models"
echo "  2. Start the backend: 'cd backend && python -m app.main'"
echo "  3. Start the frontend: 'cd frontend && npm start'" 