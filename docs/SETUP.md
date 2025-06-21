# 🛠️ Setup Guide - Valper AI Assistant

Esta guía te ayudará a configurar y ejecutar Valper AI Assistant en tu sistema con Python 3.11+ y soporte GPU optimizado.

## 📋 Prerrequisitos

### Sistema Operativo
- **macOS** (probado en 10.15+)
- **Linux** (Ubuntu 20.04+, Debian 11+)
- **Windows** (WSL2 recomendado)

### Software Requerido
- **Python 3.11+** 🚨 **REQUERIDO** ([descargar](https://www.python.org/downloads/))
- **Node.js 16+** ([descargar](https://nodejs.org/))
- **Git** ([descargar](https://git-scm.com/downloads))

### Hardware Recomendado
- **RAM**: 8GB mínimo (16GB recomendado)
- **Almacenamiento**: 3GB libres para modelos y entorno
- **GPU**: NVIDIA GPU con CUDA 11.8+ (opcional pero recomendado)
- **Micrófono**: Para funcionalidad de voz

### Instalación de Python 3.11+

#### macOS
```bash
# Con Homebrew
brew install python@3.11

# O descargar desde python.org
# https://www.python.org/downloads/
```

#### Ubuntu/Debian
```bash
# Ubuntu 22.04+ o Debian 12+
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Para versiones anteriores, usar deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

#### Windows
- Descargar desde [python.org](https://www.python.org/downloads/)
- O usar WSL2 con Ubuntu 22.04+

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/valper-ai.git
cd valper-ai
```

### 2. Configuración Automática con Entorno Aislado

```bash
# Hacer ejecutables los scripts
chmod +x scripts/*.sh

# Configurar entorno Python 3.11+ con detección automática de GPU
./scripts/setup_environment.sh
```

**Este script hará automáticamente:**
- ✅ Verificar Python 3.11+
- ✅ Crear entorno virtual aislado
- ✅ Detectar y configurar GPU (CUDA) si está disponible
- ✅ Instalar PyTorch con soporte CUDA apropiado
- ✅ Instalar todas las dependencias optimizadas
- ✅ Crear archivo de configuración `.env`
- ✅ Configurar script de activación personalizado

### 3. Descargar Modelos de IA

```bash
# Descargar modelos de IA (puede tomar varios minutos)
./scripts/setup_models.sh
```

### 4. Iniciar la Aplicación

```bash
# Activar entorno (cada vez que abras una nueva terminal)
source ./activate_valper.sh

# Terminal 1: Backend
./scripts/start_backend.sh

# Terminal 2: Frontend (nueva terminal)
source ./activate_valper.sh  # Activar entorno también aquí
./scripts/start_frontend.sh
```

### 5. Verificar Instalación

1. Abre http://localhost:3000
2. Verifica que los chips de estado muestren "Ready"
3. Prueba el botón "Test TTS"
4. Graba un mensaje de voz

## 🎮 Optimización GPU

El script detecta automáticamente tu GPU y configura:

### NVIDIA GPU Detectada
- ✅ PyTorch con CUDA 11.8
- ✅ Librerías de aceleración GPU
- ✅ Configuración optimizada para tu tarjeta

### CPU Solamente
- ✅ PyTorch optimizado para CPU
- ✅ Configuración eficiente sin GPU

### Verificar GPU
```bash
# Activar entorno
source ./activate_valper.sh

# El script mostrará automáticamente el estado de tu GPU
# También puedes verificar manualmente:
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 🔄 Activación del Entorno

### Primera vez (después del setup)
```bash
source ./activate_valper.sh
```

### Script de activación personalizado
El script `activate_valper.sh` te muestra:
- ✅ Estado del entorno Python
- ✅ Información de GPU/CUDA
- ✅ Estado de modelos descargados
- ✅ Estado de servicios corriendo
- ✅ Comandos disponibles

## 🐳 Instalación con Docker (Alternativa)

### Prerrequisitos Docker
- Docker Engine 20.10+
- Docker Compose V2
- NVIDIA Docker (para soporte GPU)

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

## 🔧 Configuración Avanzada

### Variables de Entorno

El archivo `.env` se crea automáticamente, pero puedes editarlo:

```bash
# Editar configuración
nano .env
```

Principales configuraciones:
- `API_HOST`: Host del backend (default: 0.0.0.0)
- `API_PORT`: Puerto del backend (default: 8000)
- `DEBUG`: Modo debug (default: false)
- `LOG_LEVEL`: Nivel de logs (INFO, DEBUG, ERROR)

### Configuración Manual de GPU

Si el script no detecta tu GPU correctamente:

```bash
# Activar entorno
source ./activate_valper.sh

# Verificar CUDA
nvidia-smi

# Reinstalar PyTorch con CUDA específico
pip uninstall torch torchaudio
pip install torch==2.1.0+cu118 torchaudio==2.1.0+cu118 --index-url https://download.pytorch.org/whl/cu118
```

## 🧪 Verificación de la Instalación

### Scripts de Verificación

```bash
# Activar entorno
source ./activate_valper.sh

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

- [ ] Python 3.11+ instalado (`python --version`)
- [ ] Entorno virtual aislado creado (`ls venv/`)
- [ ] GPU detectada correctamente (si disponible)
- [ ] PyTorch con CUDA funcionando (`python -c "import torch; print(torch.cuda.is_available())"`)
- [ ] Dependencias instaladas (`pip list | grep fastapi`)
- [ ] Modelos descargados (`ls models/`)
- [ ] Backend funcionando (`curl localhost:8000/health`)
- [ ] Frontend funcionando (`curl localhost:3000`)
- [ ] Micrófono accesible (permisos del navegador)

## 🚨 Solución de Problemas

### Error: Python 3.11+ no encontrado
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Verificar instalación
python3.11 --version
```

### Error: GPU no detectada
```bash
# Verificar drivers NVIDIA
nvidia-smi

# Reinstalar CUDA toolkit si es necesario
sudo apt install nvidia-cuda-toolkit

# Reejecutar setup
./scripts/setup_environment.sh
```

### Error: Conflictos con otros proyectos
```bash
# El entorno está completamente aislado, pero si hay problemas:
rm -rf venv
./scripts/setup_environment.sh
```

### Error: "Permission denied"
```bash
# Dar permisos a todos los scripts
chmod +x scripts/*.sh activate_valper.sh

# Verificar propiedad
ls -la scripts/
```

### Logs de Depuración

```bash
# Ver logs del backend
tail -f logs/valper.log

# Ver información del entorno
cat logs/environment_info.txt

# Activar modo debug
export DEBUG=true
source ./activate_valper.sh
./scripts/start_backend.sh
```

## 📊 Monitoreo del Sistema

### El script de activación muestra automáticamente:
- ✅ Estado de Python y entorno virtual
- ✅ Estado de GPU y CUDA
- ✅ Modelos descargados
- ✅ Servicios corriendo
- ✅ Puertos en uso

### Monitoreo manual:
```bash
# Uso de GPU
nvidia-smi

# Uso de memoria
htop

# Estado de servicios
source ./activate_valper.sh  # Muestra estado completo
```

## 🔄 Actualización

### Actualizar el Código

```bash
# Obtener últimos cambios
git pull origin main

# Reactivar entorno actualizado
source ./activate_valper.sh

# Actualizar dependencias si es necesario
pip install -r backend/requirements.txt

# Reiniciar servicios
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

## 🎯 Siguientes Pasos

Una vez que tengas Valper funcionando:

1. **Explora la API**: http://localhost:8000/docs
2. **Personaliza voces**: Modifica `TTSService` 
3. **Integra LLM**: Añade ChatGPT/Claude al endpoint de conversación
4. **Optimiza GPU**: Experimenta con diferentes configuraciones CUDA
5. **Despliega en producción**: Usa Docker en un servidor
6. **Contribuye**: Envía PRs con mejoras

## 📞 Soporte

Si encuentras problemas:

1. Ejecuta `source ./activate_valper.sh` para ver estado completo
2. Revisa `logs/environment_info.txt` para información técnica
3. Consulta la documentación en `docs/`
4. Busca en issues de GitHub
5. Crea un nuevo issue con logs detallados

## 💡 Beneficios del Entorno Aislado

✅ **Sin conflictos**: Tu GPU y dependencias están aisladas  
✅ **Optimizado**: PyTorch configurado específicamente para tu hardware  
✅ **Reproducible**: Mismas versiones en cualquier máquina  
✅ **Fácil cleanup**: `rm -rf venv` para empezar de cero  
✅ **Estado visible**: El script de activación muestra todo el estado  

¡Disfruta usando Valper AI Assistant! 🎉 