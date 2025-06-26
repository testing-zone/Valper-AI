#!/bin/bash
echo "🔊 Activating TTS (Kokoro) environment..."
source venv_tts/bin/activate
echo "✅ TTS environment activated!"
echo "📍 Python: $(which python)"
echo "📍 Models directory: $(pwd)/models/tts"
echo ""
