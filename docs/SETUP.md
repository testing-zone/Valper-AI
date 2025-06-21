# 🛠️ Setup Guide - Valper AI Assistant

Esta guía te ayudará a configurar y ejecutar Valper AI Assistant en tu sistema.

## 📋 Prerrequisitos

### Sistema Operativo
- **macOS** (probado en 10.15+)
- **Linux** (Ubuntu 18.04+, Debian 10+)
- **Windows** (WSL2 recomendado)

### Software Requerido
- **Python 3.8+** ([descargar](https://www.python.org/downloads/))
- **Node.js 16+** ([descargar](https://nodejs.org/))
- **Git** ([descargar](https://git-scm.com/downloads))

### Hardware Recomendado
- **RAM**: 8GB mínimo (16GB recomendado)
- **Almacenamiento**: 2GB libres para modelos
- **GPU**: NVIDIA GPU opcional (acelera TTS)
- **Micrófono**: Para funcionalidad de voz

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/valper-ai.git
cd valper-ai
```

### 2. Configuración Automática

```bash
# Hacer ejecutables los scripts
chmod +x scripts/*.sh

# Configurar entorno Python
./scripts/setup_environment.sh

# Descargar modelos de IA (puede tomar varios minutos)
./scripts/setup_models.sh
```

### 3. Iniciar la Aplicación

```bash
# Terminal 1: Backend
./scripts/start_backend.sh

# Terminal 2: Frontend (nueva terminal)
./scripts/start_frontend.sh
```

### 4. Verificar Instalación

1. Abre http://localhost:3000
2. Verifica que los chips de estado muestren "Ready"
3. Prueba el botón "Test TTS"
4. Graba un mensaje de voz

## 🐳 Instalación con Docker

### Prerrequisitos Docker
- Docker Engine 20.10+
- Docker Compose V2

### Ejecutar con Docker

```bash
# Clonar y navegar al proyecto
git clone https://github.com/tu-usuario/valper-ai.git
cd valper-ai

# Construir y ejecutar
cd docker
docker-compose up --build

# En segundo plano
docker-compose up -d --build
```

### Acceder a la Aplicación
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs

## 🔧 Configuración Detallada

### Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar configuración
nano .env
```

Principales configuraciones:
- `API_HOST`: Host del backend (default: 0.0.0.0)
- `API_PORT`: Puerto del backend (default: 8000)
- `DEBUG`: Modo debug (default: false)
- `LOG_LEVEL`: Nivel de logs (INFO, DEBUG, ERROR)

### Configuración de GPU (Opcional)

Para acelerar el procesamiento con GPU NVIDIA:

```bash
# Instalar CUDA toolkit
sudo apt install nvidia-cuda-toolkit

# Verificar instalación
nvidia-smi

# Reinstalar PyTorch con soporte CUDA
source venv/bin/activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Configuración de Audio

#### macOS
```bash
# Instalar dependencias con Homebrew
brew install portaudio espeak-ng
```

#### Ubuntu/Debian
```bash
# Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install portaudio19-dev espeak-ng
```

#### Windows (WSL2)
```bash
# En WSL2 Ubuntu
sudo apt-get install portaudio19-dev espeak-ng
```

## 🧪 Verificación de la Instalación

### Scripts de Verificación

```bash
# Verificar servicios del backend
curl http://localhost:8000/health

# Verificar frontend
curl http://localhost:3000

# Probar STT con audio de ejemplo
curl -X POST "http://localhost:8000/api/v1/stt" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@models/audio/2830-3980-0043.wav"
```

### Checklist de Verificación

- [ ] Python 3.8+ instalado (`python3 --version`)
- [ ] Node.js 16+ instalado (`node --version`)
- [ ] Entorno virtual creado (`ls venv/`)
- [ ] Dependencias Python instaladas (`pip list | grep fastapi`)
- [ ] Modelos descargados (`ls models/`)
- [ ] Backend funcionando (`curl localhost:8000/health`)
- [ ] Frontend funcionando (`curl localhost:3000`)
- [ ] Micrófono accesible (permisos del navegador)
- [ ] Audio de prueba funciona

## 🚨 Solución de Problemas

### Problemas Comunes

#### Error: "Command not found"
```bash
# Verificar PATH
echo $PATH

# Reinstalar herramientas
./scripts/setup_environment.sh
```

#### Error: "Permission denied"
```bash
# Dar permisos a scripts
chmod +x scripts/*.sh

# Verificar propiedad de archivos
ls -la scripts/
```

#### Error: "Port already in use"
```bash
# Encontrar proceso usando el puerto
lsof -i :8000
lsof -i :3000

# Terminar proceso
kill -9 [PID]
```

#### Error: "Model file not found"
```bash
# Re-descargar modelos
rm -rf models/
./scripts/setup_models.sh
```

#### Error: "Module not found"
```bash
# Activar entorno virtual
source venv/bin/activate

# Reinstalar dependencias
pip install -r backend/requirements.txt
```

#### Error de Audio/Micrófono
```bash
# Verificar dispositivos de audio (Linux)
arecord -l

# Probar grabación
arecord -d 3 test.wav

# Verificar permisos (navegador)
# Chrome: chrome://settings/content/microphone
```

### Logs de Depuración

```bash
# Logs del backend
tail -f logs/valper.log

# Logs con más detalle
export LOG_LEVEL=DEBUG
./scripts/start_backend.sh

# Logs de Docker
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Modo de Desarrollo

```bash
# Backend en modo debug
source venv/bin/activate
cd backend
export DEBUG=true
python -m uvicorn app.main:app --reload

# Frontend en modo desarrollo
cd frontend
npm start
```

## 📊 Monitoreo del Sistema

### Métricas de Rendimiento

```bash
# Uso de CPU y memoria
htop

# Uso de GPU (si disponible)
nvidia-smi

# Espacio en disco
df -h
```

### Health Checks

```bash
# Estado de servicios
curl http://localhost:8000/health | jq

# Métricas detalladas
curl http://localhost:8000/metrics
```

## 🔄 Actualización

### Actualizar el Código

```bash
# Obtener últimos cambios
git pull origin main

# Actualizar dependencias Python
source venv/bin/activate
pip install -r backend/requirements.txt

# Actualizar dependencias Node.js
cd frontend
npm install

# Reiniciar servicios
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

### Actualizar Modelos

```bash
# Re-descargar modelos
rm -rf models/
./scripts/setup_models.sh
```

## 🎯 Siguientes Pasos

Una vez que tengas Valper funcionando:

1. **Explora la API**: http://localhost:8000/docs
2. **Personaliza voces**: Modifica `TTSService` 
3. **Integra LLM**: Añade ChatGPT/Claude al endpoint de conversación
4. **Despliega en producción**: Usa Docker en un servidor
5. **Contribuye**: Envía PRs con mejoras

## 📞 Soporte

Si encuentras problemas:

1. Revisa esta guía de setup
2. Consulta la documentación en `docs/`
3. Busca en issues de GitHub
4. Crea un nuevo issue con logs detallados

¡Disfruta usando Valper AI Assistant! 🎉 