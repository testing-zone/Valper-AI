# 🚀 Guía de Instalación Completa - Valper AI

Esta guía te permite instalar **Valper AI** desde cero en una VM nueva de Ubuntu. Cada paso está probado y documentado para garantizar una instalación exitosa.

## 📋 Prerrequisitos del Sistema

### Sistema Operativo
- **Ubuntu 20.04+ LTS** (recomendado Ubuntu 22.04)
- **8GB RAM mínimo** (16GB recomendado)
- **3GB espacio libre** para modelos y dependencias
- **Acceso sudo** para configurar servicios

### Puertos Requeridos
- **3000**: Frontend React
- **8000**: Backend FastAPI  
- **80**: HTTP (Nginx)
- **443**: HTTPS (Nginx)

## 🔧 Paso 1: Preparación del Sistema

### Actualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential
```

### Instalar Python 3.11+
```bash
# Agregar repositorio deadsnakes para Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Instalar Python 3.11 y herramientas
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils
sudo apt install -y python3-pip

# Verificar instalación
python3.11 --version
```

### Instalar Node.js 18+
```bash
# Instalar NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar instalación
node --version
npm --version
```

### Instalar Nginx
```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Configurar Firewall UFW
```bash
# Habilitar UFW
sudo ufw enable

# Abrir puertos necesarios
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

# Verificar reglas
sudo ufw status
```

## 📥 Paso 2: Descargar e Instalar Valper AI

### Clonar Repositorio
```bash
cd ~
git clone https://github.com/tu-usuario/valper-ai.git
cd valper-ai
```

### Hacer Scripts Ejecutables
```bash
chmod +x setup_valper_ai.sh
chmod +x scripts/*.sh
chmod +x activate_tts.sh
```

## 🔨 Paso 3: Configuración de Entornos Virtuales

### Configurar Entorno STT (OpenAI Whisper)
```bash
./scripts/setup_stt_environment.sh
```

**Este script hace:**
- Crea `venv_stt` con Python 3.11
- Instala OpenAI Whisper y dependencias
- Descarga modelo base de Whisper
- Configura variables de entorno

### Configurar Entorno TTS (Kokoro)  
```bash
./scripts/setup_tts_environment.sh
```

**Este script hace:**
- Crea `venv_tts` con Python 3.11  
- Instala Kokoro TTS y PyTorch
- Descarga modelos Kokoro
- Configura voces disponibles

### Configurar Entorno Backend
```bash
./scripts/setup_environment.sh
```

**Este script hace:**
- Crea `venv_backend` con Python 3.11
- Instala FastAPI, Uvicorn y dependencias
- Configura integración con STT/TTS
- Prepara configuración de API

## ⚙️ Paso 4: Configuración de Backend

### Crear Archivo de Entorno
```bash
cd backend
cat > .env << EOF
TOTALGPT_API_KEY=sk-B-hP0huha1Z7nimfRFF69A
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
EOF
```

### Actualizar Requirements del Backend
```bash
cat > requirements.txt << 'EOF'
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0
pydantic==2.5.0

# Audio processing
numpy==1.24.3
soundfile==0.12.1

# AI models y APIs
openai-whisper>=20231117
kokoro>=0.9.2
requests>=2.31.0

# Environment y utilities
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2

# Additional audio processing
librosa>=0.10.1
scipy>=1.11.0

# Performance monitoring
psutil>=5.9.0

# CORS para frontend
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
EOF
```

### Instalar Dependencias Backend
```bash
# Activar entorno virtual del backend
source ../venv_backend/bin/activate

# Instalar requirements
pip install -r requirements.txt

# Verificar instalación
python -c "import fastapi, uvicorn; print('Backend dependencies OK')"

cd ..
```

## 🌐 Paso 5: Configuración de Frontend

### Instalar Dependencias Frontend
```bash
cd frontend
npm install

# Verificar instalación
npm ls react react-dom
cd ..
```

### Actualizar package.json del Frontend
```bash
cd frontend
cat > package.json << 'EOF'
{
  "name": "valper-frontend",
  "version": "2.0.0",
  "description": "Valper AI Assistant Frontend - Cyberpunk Voice Interface",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "@craco/craco": "^7.1.0",
    "axios": "^1.6.0",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "GENERATE_SOURCEMAP=false craco start",
    "build": "craco build",
    "test": "craco test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "homepage": "."
}
EOF

npm install
cd ..
```

## 🔒 Paso 6: Configuración HTTPS y SSL

### Crear Certificados SSL
```bash
# Crear directorio para certificados
sudo mkdir -p /etc/ssl/valper

# Generar certificado autofirmado (reemplaza TU_IP con tu IP real)
TU_IP="209.137.198.189"  # Cambia por tu IP

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/valper/valper.key \
  -out /etc/ssl/valper/valper.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=$TU_IP" \
  -addext "subjectAltName=IP:$TU_IP,DNS:localhost,DNS:valper-ai.local"

# Verificar certificados
sudo ls -la /etc/ssl/valper/
```

### Configurar Nginx
```bash
# Crear configuración de Nginx
sudo tee /etc/nginx/sites-available/valper-ai << EOF
# Valper AI - Production Configuration
server {
    listen 80;
    server_name _;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/valper/valper.crt;
    ssl_certificate_key /etc/ssl/valper/valper.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Frontend (React)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, Content-Type, Accept, Authorization";
    }
    
    # Backend Health y Docs
    location ~ ^/(health|docs|redoc|openapi.json) {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/valper-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Probar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

## 📝 Paso 7: Crear Scripts de Inicio

### Script de Inicio del Backend
```bash
cat > scripts/start_backend.sh << 'EOF'
#!/bin/bash

# Valper AI Backend Startup Script
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_PATH="$PROJECT_ROOT/venv_backend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Valper AI Backend...${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Backend virtual environment not found at $VENV_PATH${NC}"
    echo "Run ./scripts/setup_environment.sh first"
    exit 1
fi

# Navigate to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found in backend directory${NC}"
    echo "Create .env file with TOTALGPT_API_KEY"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start the backend server
echo -e "${GREEN}🖥️  Starting FastAPI server on http://0.0.0.0:8000${NC}"
echo "API Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF

chmod +x scripts/start_backend.sh
```

### Script de Inicio del Frontend
```bash
cat > scripts/start_frontend.sh << 'EOF'
#!/bin/bash

# Valper AI Frontend Startup Script
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🌐 Starting Valper AI Frontend...${NC}"

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    npm install
fi

# Set environment variables for React
export GENERATE_SOURCEMAP=false
export BROWSER=none

# Start the development server
echo -e "${GREEN}🚀 Starting React development server on http://localhost:3000${NC}"
echo "Cyberpunk Interface: https://your-ip (with HTTPS for microphone)"
echo "Press Ctrl+C to stop"
echo ""

exec npm start
EOF

chmod +x scripts/start_frontend.sh
```

## 🧪 Paso 8: Verificación de la Instalación

### Script de Prueba Completo
```bash
cat > scripts/test_complete_installation.sh << 'EOF'
#!/bin/bash

# Valper AI Complete Installation Test
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing Valper AI Complete Installation${NC}"
echo "==========================================="

# Test 1: Virtual Environments
echo -e "\n${BLUE}📦 Testing Virtual Environments...${NC}"
for venv in venv_stt venv_tts venv_backend; do
    if [ -d "$venv" ]; then
        echo -e "${GREEN}✅ $venv exists${NC}"
    else
        echo -e "${RED}❌ $venv missing${NC}"
    fi
done

# Test 2: Backend Dependencies
echo -e "\n${BLUE}🔧 Testing Backend Dependencies...${NC}"
source venv_backend/bin/activate
python -c "
try:
    import fastapi, uvicorn, whisper, requests
    from dotenv import load_dotenv
    print('✅ Core backend dependencies OK')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
" 2>/dev/null || echo -e "${RED}❌ Backend dependencies failed${NC}"

# Test 3: Frontend Dependencies  
echo -e "\n${BLUE}🌐 Testing Frontend Dependencies...${NC}"
cd frontend
if [ -f "package.json" ] && [ -d "node_modules" ]; then
    echo -e "${GREEN}✅ Frontend dependencies OK${NC}"
else
    echo -e "${RED}❌ Frontend dependencies missing${NC}"
fi
cd ..

# Test 4: SSL Certificates
echo -e "\n${BLUE}🔒 Testing SSL Configuration...${NC}"
if sudo test -f "/etc/ssl/valper/valper.crt" && sudo test -f "/etc/ssl/valper/valper.key"; then
    echo -e "${GREEN}✅ SSL certificates exist${NC}"
else
    echo -e "${RED}❌ SSL certificates missing${NC}"
fi

# Test 5: Nginx Configuration
echo -e "\n${BLUE}🌍 Testing Nginx Configuration...${NC}"
if sudo nginx -t &>/dev/null; then
    echo -e "${GREEN}✅ Nginx configuration valid${NC}"
else
    echo -e "${RED}❌ Nginx configuration invalid${NC}"
fi

# Test 6: Firewall Rules
echo -e "\n${BLUE}🔥 Testing Firewall Rules...${NC}"
if sudo ufw status | grep -q "80/tcp.*ALLOW" && sudo ufw status | grep -q "443/tcp.*ALLOW"; then
    echo -e "${GREEN}✅ Required ports are open${NC}"
else
    echo -e "${YELLOW}⚠️  Check firewall rules${NC}"
fi

# Test 7: Environment File
echo -e "\n${BLUE}⚙️ Testing Backend Configuration...${NC}"
if [ -f "backend/.env" ]; then
    if grep -q "TOTALGPT_API_KEY" backend/.env; then
        echo -e "${GREEN}✅ Backend .env file configured${NC}"
    else
        echo -e "${YELLOW}⚠️  TOTALGPT_API_KEY not found in .env${NC}"
    fi
else
    echo -e "${RED}❌ Backend .env file missing${NC}"
fi

echo -e "\n${BLUE}📋 Installation Test Complete${NC}"
echo "============================================"
echo -e "${GREEN}Ready to start Valper AI!${NC}"
echo ""
echo "Next steps:"
echo "1. ./scripts/start_backend.sh    # Terminal 1"
echo "2. ./scripts/start_frontend.sh   # Terminal 2"
echo "3. Visit: https://your-ip"
EOF

chmod +x scripts/test_complete_installation.sh
```

## 🚀 Paso 9: Iniciar Valper AI

### Ejecutar Pruebas
```bash
./scripts/test_complete_installation.sh
```

### Iniciar Servicios
```bash
# Terminal 1: Backend
./scripts/start_backend.sh

# Terminal 2: Frontend (nueva terminal)
./scripts/start_frontend.sh
```

### Verificar Funcionamiento
1. **Backend**: http://localhost:8000/docs
2. **Frontend**: http://localhost:3000  
3. **HTTPS**: https://TU_IP (reemplaza con tu IP real)

## 🎯 Acceso Final

### URLs de Acceso
- **Aplicación Principal**: `https://TU_IP`
- **API Documentation**: `http://TU_IP/docs`
- **Health Check**: `http://TU_IP/health`

### Verificar Estado
- Los chips deben mostrar "Ready" 
- El botón principal debe estar en azul (START)
- No debe haber errores en la consola del navegador

## 🔧 Solución de Problemas

### Backend no inicia
```bash
# Verificar entorno virtual
source venv_backend/bin/activate
pip list | grep fastapi

# Verificar .env
cat backend/.env

# Verificar logs
./scripts/start_backend.sh
```

### Frontend no carga
```bash
# Reinstalar dependencias
cd frontend
rm -rf node_modules package-lock.json
npm install

# Verificar puerto
netstat -tulpn | grep :3000
```

### HTTPS no funciona
```bash
# Verificar certificados
sudo ls -la /etc/ssl/valper/

# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Recrear certificados si es necesario
sudo rm -rf /etc/ssl/valper/*
# Volver a ejecutar creación de certificados
```

### Sin acceso al micrófono
- Verificar que estás usando HTTPS
- Aceptar el certificado autofirmado en el navegador
- Verificar permisos del navegador para el micrófono

---

**🎉 ¡Instalación Completa!** Tu Valper AI está listo para usar. 