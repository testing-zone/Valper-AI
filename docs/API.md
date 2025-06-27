# 📡 API Reference - Valper AI v2.0

Documentación completa de la API REST de **Valper AI Assistant** con integración TotalGPT, OpenAI Whisper y Kokoro TTS.

## 🌐 Información General

- **Base URL**: `http://localhost:8000` (desarrollo) / `https://tu-ip` (producción)
- **Documentación Interactiva**: `/docs` (Swagger UI)
- **Documentación Alternativa**: `/redoc` (ReDoc)
- **Esquema OpenAPI**: `/openapi.json`

## 🔐 Autenticación

La API actualmente **no requiere autenticación** para facilitar el desarrollo. En producción se recomienda implementar autenticación mediante JWT tokens.

## 📊 Endpoints

### 🏥 Health Check

#### `GET /health`

Verificar el estado de salud de todos los servicios.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-27T15:30:00Z",
  "services": {
    "stt": {
      "status": "ready",
      "model": "OpenAI Whisper base",
      "last_check": "2024-06-27T15:30:00Z"
    },
    "tts": {
      "status": "ready", 
      "model": "Kokoro TTS",
      "voices_available": 5,
      "last_check": "2024-06-27T15:30:00Z"
    },
    "llm": {
      "status": "ready",
      "model": "Sao10K-72B-Qwen2.5-Kunou-v1-FP8-Dynamic",
      "api_configured": true,
      "last_check": "2024-06-27T15:30:00Z"
    }
  },
  "version": "2.0.0"
}
```

**Códigos de Estado:**
- `200`: Todos los servicios funcionando
- `503`: Uno o más servicios no disponibles

---

### 🎤 Speech-to-Text (STT)

#### `POST /api/v1/stt`

Convertir audio a texto usando OpenAI Whisper.

**Content-Type**: `multipart/form-data`

**Parámetros:**
- `audio` (file, requerido): Archivo de audio (WAV, MP3, OGG, M4A)
- `language` (string, opcional): Código de idioma ISO 639-1 (ej: "es", "en")

**Ejemplo de Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/stt" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@mi_audio.wav" \
  -F "language=es"
```

**Respuesta:**
```json
{
  "text": "Hola, ¿cómo estás?",
  "language": "es",
  "confidence": 0.95,
  "duration": 2.3,
  "processing_time": 0.8,
  "segments": [
    {
      "start": 0.0,
      "end": 2.3,
      "text": "Hola, ¿cómo estás?"
    }
  ]
}
```

**Códigos de Estado:**
- `200`: Transcripción exitosa
- `400`: Archivo de audio inválido
- `422`: Parámetros incorrectos
- `500`: Error interno del servicio STT

---

### 🔊 Text-to-Speech (TTS)

#### `POST /api/v1/tts`

Convertir texto a audio usando Kokoro TTS.

**Content-Type**: `application/json`

**Body:**
```json
{
  "text": "Hola, soy Valper AI",
  "voice": "af_heart",
  "speed": 1.0
}
```

**Parámetros:**
- `text` (string, requerido): Texto a sintetizar (máximo 5000 caracteres)
- `voice` (string, opcional): ID de voz (default: "af_heart")
- `speed` (float, opcional): Velocidad de habla (0.5-2.0, default: 1.0)

**Voces Disponibles:**
- `af_heart` - Voz femenina suave y cálida
- `af_sky` - Voz femenina clara y brillante
- `af_light` - Voz femenina ligera y juvenil
- `am_adam` - Voz masculina profunda y madura
- `am_michael` - Voz masculina natural y equilibrada

**Respuesta:**
```json
{
  "message": "Audio generated successfully",
  "voice": "af_heart",
  "duration": 3.2,
  "text_length": 20,
  "processing_time": 1.1,
  "audio_url": "/temp/audio_12345.wav"
}
```

**Para obtener el audio:**
```bash
# El audio se devuelve como stream de bytes
curl -X POST "http://localhost:8000/api/v1/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo", "voice": "af_heart"}' \
  --output audio.wav
```

**Códigos de Estado:**
- `200`: Audio generado exitosamente
- `400`: Texto demasiado largo o voz inválida
- `422`: Parámetros incorrectos
- `500`: Error interno del servicio TTS

---

### 🎭 Gestión de Voces

#### `GET /api/v1/voices`

Obtener lista de voces disponibles para TTS.

**Respuesta:**
```json
{
  "voices": [
    {
      "id": "af_heart",
      "name": "Heart",
      "gender": "female",
      "language": "japanese",
      "description": "Voz femenina suave y cálida",
      "sample_url": "/samples/af_heart.wav"
    },
    {
      "id": "af_sky", 
      "name": "Sky",
      "gender": "female",
      "language": "japanese",
      "description": "Voz femenina clara y brillante",
      "sample_url": "/samples/af_sky.wav"
    },
    {
      "id": "am_adam",
      "name": "Adam", 
      "gender": "male",
      "language": "japanese",
      "description": "Voz masculina profunda y madura",
      "sample_url": "/samples/am_adam.wav"
    }
  ],
  "total": 5,
  "default_voice": "af_heart"
}
```

---

### 💬 Conversación Completa

#### `POST /api/v1/conversation`

Endpoint principal que combina STT → LLM → TTS para conversación completa.

**Content-Type**: `multipart/form-data`

**Parámetros:**
- `audio` (file, requerido): Archivo de audio con el mensaje del usuario
- `voice` (string, opcional): Voz para la respuesta (default: "af_heart")
- `conversation_id` (string, opcional): ID para mantener contexto de conversación

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversation" \
  -F "audio=@mi_pregunta.wav" \
  -F "voice=af_heart" \
  -F "conversation_id=session_123"
```

**Respuesta:**
```json
{
  "conversation_id": "session_123",
  "user_message": {
    "text": "¿Cuál es la capital de Francia?",
    "audio_duration": 2.1,
    "confidence": 0.98
  },
  "ai_response": {
    "text": "La capital de Francia es París. Es conocida como la Ciudad de la Luz y es famosa por sus monumentos como la Torre Eiffel y el Museo del Louvre.",
    "audio_duration": 5.8,
    "voice": "af_heart",
    "model": "Sao10K-72B-Qwen2.5-Kunou-v1-FP8-Dynamic"
  },
  "processing_time": {
    "stt": 0.8,
    "llm": 2.1,
    "tts": 1.2,
    "total": 4.1
  },
  "timestamp": "2024-06-27T15:30:00Z"
}
```

**El audio de respuesta se incluye como stream de bytes en la respuesta.**

**Códigos de Estado:**
- `200`: Conversación procesada exitosamente
- `400`: Audio inválido o parámetros incorrectos
- `503`: Uno o más servicios no disponibles

---

### 🧠 Chat Solo (LLM)

#### `POST /api/v1/chat`

Enviar mensaje de texto directamente al LLM sin STT/TTS.

**Content-Type**: `application/json`

**Body:**
```json
{
  "message": "Explícame la inteligencia artificial",
  "conversation_id": "session_123",
  "max_tokens": 500,
  "temperature": 0.7
}
```

**Parámetros:**
- `message` (string, requerido): Mensaje del usuario
- `conversation_id` (string, opcional): ID para contexto
- `max_tokens` (int, opcional): Máximo tokens en respuesta (default: 500)
- `temperature` (float, opcional): Creatividad de respuesta 0.0-1.0 (default: 0.7)

**Respuesta:**
```json
{
  "response": "La inteligencia artificial es una rama de la informática que busca crear sistemas capaces de realizar tareas que normalmente requieren inteligencia humana...",
  "conversation_id": "session_123",
  "model": "Sao10K-72B-Qwen2.5-Kunou-v1-FP8-Dynamic",
  "tokens_used": {
    "prompt": 25,
    "completion": 156,
    "total": 181
  },
  "processing_time": 1.8,
  "timestamp": "2024-06-27T15:30:00Z"
}
```

---

### 📊 Estadísticas

#### `GET /api/v1/stats`

Obtener estadísticas de uso de la API.

**Respuesta:**
```json
{
  "uptime": "2 days, 14:32:10",
  "requests": {
    "total": 1247,
    "stt": 523,
    "tts": 498,
    "conversation": 215,
    "chat": 11
  },
  "average_processing_time": {
    "stt": 0.85,
    "tts": 1.2,
    "llm": 2.1,
    "conversation": 4.15
  },
  "models_status": {
    "whisper": "loaded",
    "kokoro": "loaded",
    "totalgpt": "connected"
  },
  "server_info": {
    "version": "2.0.0",
    "python_version": "3.11.4",
    "platform": "Linux-6.8.0-45-generic"
  }
}
```

---

## 📝 Esquemas de Datos

### TTSRequest
```json
{
  "text": "string (1-5000 chars)",
  "voice": "string (optional)",
  "speed": "float (0.5-2.0, optional)"
}
```

### ConversationResponse
```json
{
  "conversation_id": "string",
  "user_message": {
    "text": "string",
    "audio_duration": "float",
    "confidence": "float"
  },
  "ai_response": {
    "text": "string", 
    "audio_duration": "float",
    "voice": "string",
    "model": "string"
  },
  "processing_time": {
    "stt": "float",
    "llm": "float", 
    "tts": "float",
    "total": "float"
  },
  "timestamp": "string (ISO 8601)"
}
```

### ServiceStatus
```json
{
  "status": "ready|loading|error",
  "model": "string",
  "last_check": "string (ISO 8601)",
  "additional_info": "object (optional)"
}
```

---

## 🚨 Códigos de Error

### Errores Comunes

#### 400 Bad Request
```json
{
  "detail": "Invalid audio format. Supported: WAV, MP3, OGG, M4A",
  "error_code": "INVALID_AUDIO_FORMAT"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "String too long (max 5000 characters)",
      "type": "value_error"
    }
  ]
}
```

#### 503 Service Unavailable
```json
{
  "detail": "TTS service temporarily unavailable",
  "error_code": "SERVICE_UNAVAILABLE",
  "retry_after": 30
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal processing error",
  "error_code": "INTERNAL_ERROR",
  "request_id": "req_12345"
}
```

---

## 🧪 Ejemplos de Uso

### Conversación Completa con cURL

```bash
#!/bin/bash

# 1. Verificar estado de servicios
curl -X GET "http://localhost:8000/health" | jq

# 2. Grabar audio y hacer conversación
curl -X POST "http://localhost:8000/api/v1/conversation" \
  -F "audio=@mi_pregunta.wav" \
  -F "voice=af_heart" \
  --output respuesta.wav

# 3. Solo TTS para prueba
curl -X POST "http://localhost:8000/api/v1/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola, soy Valper AI", "voice": "af_heart"}' \
  --output saludo.wav

# 4. Chat de texto
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es la IA?"}' | jq
```

### Ejemplo con Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Health check
health = requests.get(f"{BASE_URL}/health")
print(f"Health: {health.json()}")

# Text-to-Speech
tts_data = {
    "text": "Hola, soy tu asistente Valper AI", 
    "voice": "af_heart"
}
tts_response = requests.post(
    f"{BASE_URL}/api/v1/tts",
    json=tts_data
)

with open("respuesta.wav", "wb") as f:
    f.write(tts_response.content)

# Chat
chat_data = {
    "message": "Explícame la computación cuántica",
    "max_tokens": 300
}
chat_response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    json=chat_data
)
print(f"Respuesta: {chat_response.json()['response']}")

# Conversación con audio
with open("mi_audio.wav", "rb") as audio_file:
    files = {"audio": audio_file}
    data = {"voice": "af_heart"}
    
    conversation_response = requests.post(
        f"{BASE_URL}/api/v1/conversation",
        files=files,
        data=data
    )
    
    # Guardar respuesta de audio
    with open("conversacion_respuesta.wav", "wb") as f:
        f.write(conversation_response.content)
```

### Ejemplo con JavaScript

```javascript
// Health check
async function checkHealth() {
  const response = await fetch('/health');
  const health = await response.json();
  console.log('Services:', health.services);
}

// Text-to-Speech
async function textToSpeech(text, voice = 'af_heart') {
  const response = await fetch('/api/v1/tts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, voice })
  });
  
  if (response.ok) {
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
  }
}

// Conversación con audio
async function conversation(audioBlob, voice = 'af_heart') {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.wav');
  formData.append('voice', voice);
  
  const response = await fetch('/api/v1/conversation', {
    method: 'POST',
    body: formData
  });
  
  if (response.ok) {
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
  }
}

// Chat de texto
async function chat(message) {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message })
  });
  
  const data = await response.json();
  return data.response;
}
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno para API

```bash
# Backend .env
TOTALGPT_API_KEY=sk-tu-api-key
API_HOST=0.0.0.0
API_PORT=8000
MAX_FILE_SIZE=10485760  # 10MB
CORS_ORIGINS=["http://localhost:3000", "https://tu-dominio.com"]
LOG_LEVEL=INFO
```

### Límites y Restricciones

- **Tamaño máximo de archivo de audio**: 10MB
- **Duración máxima de audio**: 10 minutos  
- **Longitud máxima de texto para TTS**: 5000 caracteres
- **Tokens máximos por request de chat**: 4000
- **Rate limiting**: 100 requests por minuto por IP

### CORS y Seguridad

La API está configurada para aceptar requests desde:
- `http://localhost:3000` (desarrollo)
- `https://tu-ip` (producción con HTTPS)

Para producción, configurar adicionalmente:
- Autenticación JWT
- Rate limiting más estricto
- Validación de input adicional
- Logs de auditoría

---

## 📚 Recursos Adicionales

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`
- **Health Endpoint**: `http://localhost:8000/health`

---

**Valper AI API v2.0** - Documentación completa para desarrolladores 🚀