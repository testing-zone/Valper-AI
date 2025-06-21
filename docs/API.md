# 📡 API Documentation - Valper AI Assistant

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required for API endpoints.

## Endpoints

### Health Check

#### `GET /health`
Check the health status of the backend services.

**Response:**
```json
{
  "status": "healthy",
  "stt_ready": true,
  "tts_ready": true
}
```

### Speech-to-Text

#### `POST /api/v1/stt`
Convert audio to text using DeepSpeech.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Audio file (WAV, MP3, etc.)

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/stt" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@recording.wav"
```

**Response:**
```json
{
  "text": "Hello, how are you today?"
}
```

**Error Responses:**
- `400`: Invalid audio file format
- `503`: STT service not available
- `500`: Transcription failed

### Text-to-Speech

#### `POST /api/v1/tts`
Convert text to speech using Kokoro.

**Request:**
- Method: `POST`
- Content-Type: `application/json`

**Body:**
```json
{
  "text": "Hello, I am Valper!",
  "voice": "af_heart"
}
```

**Parameters:**
- `text` (string, required): Text to synthesize (max 1000 characters)
- `voice` (string, optional): Voice to use (default: "af_heart")

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "af_heart"}' \
  --output speech.wav
```

**Response:**
- Content-Type: `audio/wav`
- Binary audio data

**Error Responses:**
- `503`: TTS service not available
- `500`: Speech synthesis failed

### Available Voices

#### `GET /api/v1/voices`
Get list of available TTS voices.

**Response:**
```json
{
  "voices": [
    "af_heart",
    "af_sky", 
    "af_light",
    "am_adam",
    "am_michael"
  ]
}
```

### Conversation

#### `POST /api/v1/conversation`
Send a message and get both text and audio response.

**Request:**
- Method: `POST`
- Content-Type: `application/json`

**Body:**
```json
{
  "message": "Hello Valper, how are you?"
}
```

**Response:**
```json
{
  "text_response": "You said: Hello Valper, how are you?. This is Valper responding!",
  "audio_url": "/api/v1/audio/temp_audio_123.wav"
}
```

### Audio File Access

#### `GET /api/v1/audio/{filename}`
Retrieve generated audio files.

**Parameters:**
- `filename` (string): Name of the audio file

**Response:**
- Content-Type: `audio/wav`
- Binary audio data

**Error Responses:**
- `404`: Audio file not found

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing:
- Request rate limits per IP
- Audio file size limits
- Text length limits

## Usage Examples

### JavaScript/Frontend

```javascript
// Speech-to-Text
const sttRequest = async (audioBlob) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'audio.wav');
  
  const response = await fetch('/api/v1/stt', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};

// Text-to-Speech
const ttsRequest = async (text, voice = 'af_heart') => {
  const response = await fetch('/api/v1/tts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, voice })
  });
  
  return await response.blob();
};

// Conversation
const conversationRequest = async (message) => {
  const response = await fetch('/api/v1/conversation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message })
  });
  
  return await response.json();
};
```

### Python

```python
import requests
import json

# Speech-to-Text
def stt_request(audio_file_path):
    with open(audio_file_path, 'rb') as f:
        files = {'audio': f}
        response = requests.post('http://localhost:8000/api/v1/stt', files=files)
    return response.json()

# Text-to-Speech
def tts_request(text, voice='af_heart'):
    data = {'text': text, 'voice': voice}
    response = requests.post(
        'http://localhost:8000/api/v1/tts',
        json=data
    )
    
    with open('output.wav', 'wb') as f:
        f.write(response.content)
    return 'output.wav'

# Conversation
def conversation_request(message):
    data = {'message': message}
    response = requests.post(
        'http://localhost:8000/api/v1/conversation',
        json=data
    )
    return response.json()
```

## WebSocket Support (Future)

Planned endpoints for real-time streaming:

```
ws://localhost:8000/ws/stt      # Real-time STT
ws://localhost:8000/ws/tts      # Real-time TTS
ws://localhost:8000/ws/chat     # Full conversation
```

## OpenAPI Schema

Full OpenAPI schema available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc  
- JSON Schema: http://localhost:8000/openapi.json 