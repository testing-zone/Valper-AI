# 🤖 Valper AI Assistant

Un asistente de voz inteligente que utiliza DeepSpeech para speech-to-text y Kokoro para text-to-speech.

## 🌟 Características

- **Speech-to-Text (STT)**: Conversión de voz a texto usando DeepSpeech
- **Text-to-Speech (TTS)**: Síntesis de voz usando Kokoro con múltiples voces
- **Interfaz Web Moderna**: Frontend React con Material-UI
- **API REST**: Backend FastAPI con documentación automática
- **Soporte Docker**: Despliegue fácil con Docker Compose
- **Tiempo Real**: Procesamiento de audio en tiempo real

## 📁 Estructura del Proyecto

```
valper-ai/
├── backend/                 # Servidor FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints de la API
│   │   ├── models/         # Esquemas Pydantic
│   │   └── services/       # Servicios STT/TTS
│   ├── requirements.txt    # Dependencias Python
│   └── config.py          # Configuración
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   └── App.js        # Componente principal
│   └── package.json      # Dependencias Node.js
├── models/                # Modelos de IA descargados
├── scripts/               # Scripts de configuración
├── docker/               # Configuración Docker
└── docs/                # Documentación
```

## 🚀 Instalación y Configuración

### Opción 1: Instalación Manual

#### 1. Configurar el Entorno

```bash
# Clonar el repositorio
git clone [tu-repo]
cd valper-ai

# Ejecutar script de configuración del entorno
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

#### 2. Descargar Modelos

```bash
# Descargar modelos de IA
chmod +x scripts/setup_models.sh
./scripts/setup_models.sh
```

#### 3. Iniciar Backend

```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor
chmod +x scripts/start_backend.sh
./scripts/start_backend.sh
```

#### 4. Configurar Frontend

```bash
# En otra terminal
cd frontend
npm install
npm start
```

### Opción 2: Docker (Recomendado)

```bash
# Construir y ejecutar con Docker Compose
cd docker
docker-compose up --build

# Solo frontend y backend
docker-compose up backend frontend

# Con proxy nginx
docker-compose --profile proxy up
```

## 🔧 Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y ajusta según tus necesidades:

```bash
cp .env.example .env
```

### Configuración de GPU

Si tienes una GPU NVIDIA, puedes optimizar el rendimiento:

```bash
# Instalar CUDA toolkit (Ubuntu/Debian)
sudo apt install nvidia-cuda-toolkit

# Para Docker con GPU
docker-compose -f docker-compose.gpu.yml up
```

## 📝 Uso

### Interfaz Web

1. Abre http://localhost:3000
2. Verifica que el backend esté funcionando (chips de estado)
3. Haz clic en "Start Recording" para grabar tu voz
4. Valper procesará tu mensaje y responderá con texto y voz

### API REST

La API está documentada automáticamente en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Endpoints Principales

```bash
# Health check
GET /health

# Speech to Text
POST /api/v1/stt
Content-Type: multipart/form-data
Body: audio file

# Text to Speech
POST /api/v1/tts
Content-Type: application/json
Body: {"text": "Hello", "voice": "af_heart"}

# Conversación
POST /api/v1/conversation
Content-Type: application/json
Body: {"message": "Hello Valper"}

# Voces disponibles
GET /api/v1/voices
```

## 🧠 Arquitectura

### Backend (FastAPI)

- **STTService**: Maneja DeepSpeech para speech-to-text
- **TTSService**: Maneja Kokoro para text-to-speech  
- **API Routes**: Endpoints REST para frontend
- **Configuración**: Variables de entorno y settings

### Frontend (React)

- **VoiceRecorder**: Captura audio del micrófono
- **ConversationHistory**: Historial de conversaciones
- **TTSPlayer**: Reproductor de audio generado
- **App**: Componente principal con lógica de estado

### Modelos de IA

- **DeepSpeech 0.9.3**: STT en inglés (~190MB)
- **Kokoro**: TTS multivoces (~82M parámetros)

## 🎯 Funcionalidades Clave

### Speech-to-Text
- Procesamiento de audio en tiempo real
- Soporte para archivos WAV, MP3
- Transcripción con confianza variable

### Text-to-Speech  
- 5 voces disponibles (af_heart, af_sky, af_light, am_adam, am_michael)
- Salida de alta calidad (24kHz)
- Generación rápida y eficiente

### Interfaz de Usuario
- Diseño responsive con Material-UI
- Tema oscuro con efectos glassmorphism
- Visualizador de ondas durante grabación
- Historial de conversaciones persistente

## 🛠️ Desarrollo

### Estructura de Servicios

```python
# STT Service
class STTService:
    async def transcribe_audio(self, audio_file_path: str) -> str
    async def transcribe_audio_stream(self, audio_data: bytes) -> str

# TTS Service  
class TTSService:
    async def synthesize_speech(self, text: str, voice: str) -> str
    async def synthesize_speech_stream(self, text: str) -> Generator
```

### Agregar Nuevas Funcionalidades

1. **Nuevo modelo TTS**: Modifica `TTSService` en `backend/app/services/tts_service.py`
2. **Nuevo endpoint**: Agrega rutas en `backend/app/api/routes.py`
3. **Componente frontend**: Crea en `frontend/src/components/`

### Testing

```bash
# Backend
cd backend
python -m pytest

# Frontend  
cd frontend
npm test
```

## 🚨 Solución de Problemas

### Problemas Comunes

**Error: "Model file not found"**
```bash
# Descargar modelos
./scripts/setup_models.sh
```

**Error: "Microphone access denied"**
- Permitir acceso al micrófono en el navegador
- Usar HTTPS para producción

**Error: "Kokoro not available"**
```bash
# Instalar Kokoro
pip install kokoro>=0.9.2
```

**Error de GPU/CUDA**
```bash
# Verificar instalación CUDA
nvidia-smi
# Reinstalar PyTorch con CUDA support
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Logs y Depuración

```bash
# Ver logs del backend
tail -f logs/valper.log

# Logs de Docker
docker-compose logs -f backend

# Debug mode
export DEBUG=true
```

## 🔮 Roadmap

- [ ] Integración con LLM (GPT, Claude, Llama)
- [ ] Soporte multiidioma
- [ ] WebRTC para streaming en tiempo real
- [ ] Clonación de voz personalizada
- [ ] Detección de actividad de voz (VAD)
- [ ] Plugin para navegadores
- [ ] App móvil React Native

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👨‍💻 Autor

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- Email: tu-email@example.com

## 🙏 Agradecimientos

- [Mozilla DeepSpeech](https://github.com/mozilla/DeepSpeech)
- [Kokoro TTS](https://github.com/yl4579/StyleTTS2)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Material-UI](https://mui.com/)

---

⭐ ¡Dale una estrella si este proyecto te ayudó! 