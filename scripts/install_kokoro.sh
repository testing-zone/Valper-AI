#!/bin/bash

# Install Kokoro TTS in backend environment

set -e

echo "🔊 Installing Kokoro TTS for backend..."

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y espeak-ng espeak-ng-data

# Activate backend environment
echo "🔄 Activating backend environment..."
source venv_backend/bin/activate

# Install Kokoro TTS
echo "📦 Installing Kokoro TTS..."
pip install kokoro>=0.9.2

# Test installation
echo "🔍 Testing Kokoro installation..."
python -c "
try:
    from kokoro import KPipeline
    print('✅ Kokoro TTS imported successfully')
    
    # Test pipeline creation
    pipeline = KPipeline(lang_code='a')
    print('✅ Kokoro pipeline created successfully')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo "✅ Kokoro TTS installation complete!" 