# 🎤 Valper AI - Asistente de Voz Inteligente

**Valper AI** es un asistente de voz completo que combina **Speech-to-Text**, **Large Language Model** y **Text-to-Speech** para crear conversaciones naturales por voz. Diseñado con una interfaz cyberpunk moderna y capacidades de IA avanzadas.

## 🌟 ¿Qué hace Valper AI?

Valper AI te permite tener **conversaciones completas por voz** con un asistente inteligente:

1. **🎤 Hablas** → El sistema convierte tu voz a texto (OpenAI Whisper)
2. **🧠 Piensa** → Un modelo de lenguaje avanzado (TotalGPT) procesa tu mensaje
3. **🔊 Responde** → Convierte la respuesta a voz natural (Kokoro TTS)
4. **🎧 Escuchas** → Reproduces la respuesta con control total de audio

### Características Principales

- **🎙️ Speech-to-Text**: OpenAI Whisper para transcripción precisa
- **🤖 LLM Integration**: TotalGPT API con modelo Sao10K-72B-Qwen2.5-Kunou-v1
- **🗣️ Text-to-Speech**: Kokoro TTS con voces naturales japonesas
- **🌐 Interfaz Moderna**: React con diseño cyberpunk y efectos visuales
- **🔒 Acceso Seguro**: HTTPS con certificados SSL para acceso al micrófono
- **⚡ Tiempo Real**: Procesamiento rápido y respuestas fluidas
- **🎵 Control de Audio**: Detener/reanudar audio en cualquier momento
- **📱 Responsive**: Funciona en desktop y móvil

## 🎯 Casos de Uso

- **Asistente Personal**: Respuestas a preguntas, información general
- **Práctica de Idiomas**: Conversaciones naturales para aprender
- **Accesibilidad**: Interfaz de voz para usuarios con discapacidades
- **Prototipado de IA**: Base para desarrollar otros asistentes de voz
- **Demostración Tecnológica**: Showcase de integración STT+LLM+TTS

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   🎤 Frontend   │◄──►│   🖥️ Backend     │◄──►│  🧠 TotalGPT   │
│   React + JS    │    │   FastAPI        │    │     API         │
│                 │    │                  │    │                 │
│  • Micrófono    │    │ • OpenAI Whisper │    │ • Sao10K-72B    │
│  • Audio Player │    │ • Kokoro TTS     │    │ • Conversación  │
│  • UI Cyberpunk │    │ • API Routes     │    │ • Context       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
          │                       │
          │                       │
          ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   🔒 HTTPS      │    │   🎵 Modelos     │
│   SSL/Nginx     │    │   • Whisper      │
│   Proxy         │    │   • Kokoro       │
└─────────────────┘    └──────────────────┘
```

## 🚀 Instalación Rápida

### Prerrequisitos
- **Ubuntu/Linux** (probado en Ubuntu 20.04+)
- **Python 3.8+**
- **Node.js 16+**
- **3GB+ espacio libre**
- **8GB+ RAM recomendado**

### Instalación en 1 Comando

```bash
# Clona y configura todo automáticamente
git clone https://github.com/tu-usuario/valper-ai.git
cd valper-ai
chmod +x setup_valper_ai.sh
./setup_valper_ai.sh
```

### Configuración Manual Rápida

```bash
# 1. Configurar entornos virtuales
./scripts/setup_stt_environment.sh    # OpenAI Whisper
./scripts/setup_tts_environment.sh    # Kokoro TTS

# 2. Configurar backend
cd backend
echo "TOTALGPT_API_KEY=tu-api-key" > .env

# 3. Instalar frontend
cd ../frontend
npm install

# 4. Iniciar servicios
./scripts/start_backend.sh &   # Terminal 1
./scripts/start_frontend.sh   # Terminal 2
```

## 🌐 Acceso a la Aplicación

Una vez instalado, puedes acceder a Valper AI en:

- **HTTP**: `http://localhost:3000` (sin micrófono)
- **HTTPS**: `https://tu-ip` (con micrófono habilitado)
- **API**: `http://localhost:8000/docs`

### Configuración HTTPS (Para Micrófono)

El acceso al micrófono requiere HTTPS. Los scripts incluyen configuración automática:

```bash
# Los certificados SSL se crean automáticamente
# Nginx se configura como proxy reverso
# Firewall se ajusta automáticamente
```

## 🎮 Cómo Usar

1. **Abre la aplicación** en tu navegador
2. **Verifica estado**: Los chips deben mostrar "Ready" 
3. **Presiona el botón central** para empezar a grabar
4. **Habla tu mensaje** (el botón se pone rosa)
5. **Espera la respuesta** (procesamiento en morado)
6. **Escucha la respuesta** (audio se reproduce automáticamente)
7. **Control total**: Presiona nuevamente para detener audio

### Estados del Botón Principal

- 🔵 **INICIAR** (Cyan) → Presiona para empezar a grabar
- 🔴 **GRABANDO** (Rosa + Pulso) → Hablando, presiona para detener
- 🟣 **PROCESANDO** (Morado + Spinner) → IA está pensando
- 🟠 **REPRODUCIENDO** (Naranja + Stop) → Audio sonando, presiona para detener

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno
- **OpenAI Whisper** - Speech-to-Text
- **Kokoro TTS** - Text-to-Speech japonés
- **TotalGPT API** - Large Language Model
- **Uvicorn** - Servidor ASGI

### Frontend  
- **React 18** - Framework frontend
- **JavaScript ES6+** - Lenguaje principal
- **MediaRecorder API** - Captura de audio
- **CSS3 Animations** - Efectos visuales
- **Custom CSS** - Diseño cyberpunk

### Infraestructura
- **Nginx** - Proxy reverso y SSL
- **UFW Firewall** - Seguridad de red  
- **SSL Certificates** - Encriptación HTTPS
- **Virtual Environments** - Aislamiento de dependencias

## 📊 Estado del Proyecto

- ✅ **STT**: OpenAI Whisper funcionando
- ✅ **TTS**: Kokoro TTS operativo  
- ✅ **LLM**: TotalGPT API integrado
- ✅ **Frontend**: Interfaz cyberpunk completa
- ✅ **HTTPS**: Certificados SSL configurados
- ✅ **Audio Control**: Start/Stop funcional
- ✅ **Despliegue**: Scripts de instalación listos

## 📚 Documentación

- **[Setup Detallado](docs/SETUP.md)** - Instalación paso a paso
- **[API Reference](docs/API.md)** - Documentación de endpoints
- **[Development](docs/README.md)** - Guía para desarrolladores

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🔧 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/valper-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tu-usuario/valper-ai/discussions)
- **Email**: soporte@valper-ai.com

---

**Valper AI** - *Tu asistente de voz del futuro* 🚀