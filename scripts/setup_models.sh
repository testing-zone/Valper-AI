#!/bin/bash

# Valper AI Assistant - Model Setup Script
# This script downloads the required models for STT and TTS

set -e

echo "🤖 Setting up Valper AI Assistant models..."

# Create models directory
mkdir -p models
cd models

echo "📥 Downloading DeepSpeech models..."

# Download DeepSpeech model files
if [ ! -f "deepspeech-0.9.3-models.pbmm" ]; then
    echo "Downloading DeepSpeech model..."
    curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
    echo "✅ DeepSpeech model downloaded"
else
    echo "✅ DeepSpeech model already exists"
fi

if [ ! -f "deepspeech-0.9.3-models.scorer" ]; then
    echo "Downloading DeepSpeech scorer..."
    curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer
    echo "✅ DeepSpeech scorer downloaded"
else
    echo "✅ DeepSpeech scorer already exists"
fi

# Download sample audio for testing
if [ ! -d "audio" ]; then
    echo "Downloading sample audio files..."
    curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/audio-0.9.3.tar.gz
    tar xvf audio-0.9.3.tar.gz
    rm audio-0.9.3.tar.gz
    echo "✅ Sample audio files downloaded"
else
    echo "✅ Sample audio files already exist"
fi

cd ..

echo "🎉 Model setup complete!"
echo ""
echo "Models downloaded:"
echo "  - DeepSpeech model: models/deepspeech-0.9.3-models.pbmm"
echo "  - DeepSpeech scorer: models/deepspeech-0.9.3-models.scorer"
echo "  - Sample audio: models/audio/"
echo ""
echo "You can now start the Valper AI Assistant backend!" 