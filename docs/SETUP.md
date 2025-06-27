# 🛠️ Setup Guide - Valper AI Assistant v2.0

Esta guía te ayudará a configurar y ejecutar **Valper AI Assistant** - un asistente de voz completo con **OpenAI Whisper**, **TotalGPT API**, y **Kokoro TTS** en tu sistema.

## 📋 Prerrequisitos

### Sistema Operativo
- **Ubuntu 20.04+ LTS** (recomendado Ubuntu 22.04)
- **Linux** con soporte para Python 3.11+
- **8GB RAM mínimo** (16GB recomendado para mejor rendimiento)

### Software Requerido
- **Python 3.11+** 🚨 **REQUERIDO** ([guía de instalación](#instalación-de-python-311))
- **Node.js 18+** ([descargar](https://nodejs.org/))
- **Git** ([descargar](https://git-scm.com/downloads))
- **Nginx** (para configuración HTTPS)

### Hardware Recomendado
- **RAM**: 8GB mínimo (16GB recomendado)
- **Almacenamiento**: 3GB libres para modelos y entorno
- **GPU**: NVIDIA GPU con CUDA (opcional, mejora rendimiento TTS)
- **Micrófono**: Requerido para funcionalidad de voz

### Requisitos de Red
- **Puertos**: 80, 443, 3000, 8000 (configurados automáticamente)
- **Firewall**: UFW recomendado
- **HTTPS**: Requerido para acceso al micrófono del navegador

## 🚀 Métodos de Instalación

### Opción 1: Instalación Automática (Recomendada)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/valper-ai.git
cd valper-ai

# Ejecutar instalación automática
chmod +x setup_quick_install.sh
./setup_quick_install.sh
```

**La instalación automática incluye:**
- ✅ Instalación de dependencias del sistema
- ✅ Configuración de Python 3.11 y entornos virtuales
- ✅ Instalación de Node.js y dependencias frontend
- ✅ Configuración de Nginx con SSL/HTTPS
- ✅ Configuración de firewall UFW
- ✅ Creación de certificados SSL autofirmados
- ✅ Scripts de inicio automáticos

### Opción 2: Instalación Manual Paso a Paso

#### 1. Preparación del Sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential

# Instalar Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# Instalar Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Instalar Nginx
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### 2. Configurar Entornos Virtuales

```bash
# Clonar proyecto
git clone https://github.com/tu-usuario/valper-ai.git
cd valper-ai

# Hacer scripts ejecutables
chmod +x scripts/*.sh

# Configurar entorno STT (OpenAI Whisper)
./scripts/setup_stt_environment.sh

# Configurar entorno TTS (Kokoro)
./scripts/setup_tts_environment.sh

# Configurar entorno Backend (FastAPI)
./scripts/setup_environment.sh
```

#### 3. Configurar Backend

```bash
cd backend

# Crear archivo .env con tu API key de TotalGPT
cat > .env << EOF
TOTALGPT_API_KEY=tu-api-key-aqui
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
EOF

# Activar entorno e instalar dependencias
source ../venv_backend/bin/activate
pip install -r requirements.txt

cd ..
```

#### 4. Configurar Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Verificar instalación
npm ls react react-dom

cd ..
```

#### 5. Configurar HTTPS/SSL

```bash
# Crear directorio para certificados
sudo mkdir -p /etc/ssl/valper

# Generar certificado SSL (reemplaza TU_IP con tu IP real)
export SERVER_IP="tu-ip-aqui"
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/valper/valper.key \
  -out /etc/ssl/valper/valper.crt \
  -subj "/C=US/ST=State/L=City/O=Valper-AI/CN=$SERVER_IP" \
  -addext "subjectAltName=IP:$SERVER_IP,DNS:localhost,DNS:valper-ai.local"
```

#### 6. Configurar Nginx

```bash
# Crear configuración de Nginx (ver docs/INSTALACION_COMPLETA.md para config completa)
sudo nano /etc/nginx/sites-available/valper-ai

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/valper-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar y recargar
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. Configurar Firewall

```bash
# Configurar UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

# Verificar reglas
sudo ufw status
```

## 🎮 Iniciar Valper AI

### Scripts de Inicio

```bash
# Terminal 1: Backend
./scripts/start_backend.sh

# Terminal 2: Frontend (nueva terminal)
./scripts/start_frontend.sh
```

### URLs de Acceso

- **Aplicación Principal**: `https://tu-ip` (recomendado para micrófono)
- **HTTP**: `http://tu-ip` (sin acceso a micrófono)
- **API Documentation**: `http://tu-ip/docs`
- **Health Check**: `http://tu-ip/health`

## 🔧 Configuración

### Variables de Entorno

El archivo `backend/.env` contiene:

```bash
# API Key de TotalGPT (REQUERIDO)
TOTALGPT_API_KEY=sk-tu-api-key

# Configuración del servidor
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### Configuración de TotalGPT API

**Valper AI utiliza TotalGPT API con el modelo:**
- **Modelo**: `Sao10K-72B-Qwen2.5-Kunou-v1-FP8-Dynamic`
- **Endpoint**: `https://api.totalgpt.ai/v1/chat/completions`
- **API Key**: Requerida en `.env`

### Personalización de Voces TTS

Las voces disponibles en Kokoro TTS:
- `af_heart` - Voz femenina suave
- `af_sky` - Voz femenina clara  
- `af_light` - Voz femenina ligera
- `am_adam` - Voz masculina profunda
- `am_michael` - Voz masculina natural

## 🧪 Verificación de la Instalación

### Script de Prueba Completo

```bash
# Ejecutar verificación completa
./scripts/test_complete_installation.sh
```

### Verificación Manual

```bash
# 1. Verificar entornos virtuales
ls -la venv_*

# 2. Verificar backend
source venv_backend/bin/activate
python -c "import fastapi, uvicorn, whisper; print('Backend OK')"

# 3. Verificar frontend
cd frontend && npm ls react

# 4. Verificar SSL
sudo ls -la /etc/ssl/valper/

# 5. Verificar Nginx
sudo nginx -t

# 6. Verificar firewall
sudo ufw status
```

## 🎯 Uso de la Aplicación

### Interfaz de Usuario Cyberpunk

**Elementos principales:**
- **Botón Central**: Control principal de voz (4 estados)
  - 🔵 **START** (Cyan) - Iniciar grabación
  - 🔴 **LISTENING** (Rosa) - Grabando audio
  - 🟣 **THINKING** (Morado) - Procesando con IA
  - 🟠 **PLAYING** (Naranja) - Reproduciendo respuesta

- **Chips de Estado**: Muestran estado de servicios STT/TTS/LLM
- **Historial**: Conversación completa con timestamps
- **Voice Synthesis Lab**: Prueba directa de TTS

### Flujo de Conversación

1. **Presiona el botón** → Comienza grabación
2. **Habla tu mensaje** → STT transcribe con Whisper
3. **Espera respuesta** → LLM procesa con TotalGPT
4. **Escucha respuesta** → TTS genera audio con Kokoro
5. **Control total** → Detener audio en cualquier momento

## 🛠️ Desarrollo

### Estructura del Proyecto

```
valper-ai/
├── backend/               # FastAPI + Servicios IA
│   ├── app/
│   │   ├── api/          # Endpoints REST
│   │   │   └── services/     # STT, TTS, LLM
│   │   ├── models/       # Esquemas Pydantic
│   │   └── services/     # STT, TTS, LLM
│   ├── .env             # Variables de entorno
│   └── requirements.txt # Dependencias Python
├── frontend/             # React + Cyberpunk UI
│   ├── src/
│   │   ├── App.js       # Componente principal
│   │   └── App.css      # Estilos cyberpunk
│   └── package.json     # Dependencias Node.js
├── scripts/             # Scripts de configuración
├── venv_*/              # Entornos virtuales
└── docs/               # Documentación
```

### Scripts Disponibles

- `setup_quick_install.sh` - Instalación completa automática
- `scripts/start_backend.sh` - Iniciar servidor FastAPI  
- `scripts/start_frontend.sh` - Iniciar aplicación React
- `scripts/test_complete_installation.sh` - Verificar instalación
- `scripts/setup_*_environment.sh` - Configurar entornos específicos

## 📊 Estado de Servicios

### Verificar Estado en Tiempo Real

```bash
# Backend status
curl http://localhost:8000/health

# Frontend status  
curl http://localhost:3000

# Nginx status
sudo systemctl status nginx

# Procesos activos
ps aux | grep -E "(uvicorn|node)"
```

### Logs y Debugging

```bash
# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs del sistema
journalctl -u nginx -f

# Debug del backend
./scripts/start_backend.sh  # Ver output en consola

# Debug del frontend
./scripts/start_frontend.sh  # Ver output en consola
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### "No se puede acceder al micrófono"
- ✅ Usar HTTPS: `https://tu-ip`
- ✅ Aceptar certificado autofirmado
- ✅ Permitir micrófono en navegador

#### "Backend no responde"
```bash
# Verificar entorno virtual
source venv_backend/bin/activate
pip list | grep fastapi

# Verificar .env
cat backend/.env

# Reinstalar dependencias
pip install -r backend/requirements.txt
```

#### "Frontend no carga"
```bash
# Limpiar cache
cd frontend
rm -rf node_modules package-lock.json
npm install

# Verificar puerto
netstat -tulpn | grep :3000
```

#### "Error SSL/HTTPS"
```bash
# Recrear certificados
sudo rm -rf /etc/ssl/valper/*
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/valper/valper.key \
  -out /etc/ssl/valper/valper.crt \
  -subj "/C=US/ST=State/L=City/O=Valper-AI/CN=$SERVER_IP" \
  -addext "subjectAltName=IP:$SERVER_IP,DNS:localhost"

# Recargar Nginx
sudo systemctl reload nginx
```

## 📚 Documentación Adicional

- **[README Principal](../README.md)** - Descripción general del proyecto
- **[Instalación Completa](INSTALACION_COMPLETA.md)** - Guía detallada paso a paso
- **[API Reference](API.md)** - Documentación de endpoints
- **[Arquitectura](README.md)** - Detalles técnicos y desarrollo

---

**🎉 ¡Valper AI listo para usar!** Tu asistente de voz del futuro está operativo. 