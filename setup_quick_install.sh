#!/bin/bash

# Valper AI - Quick Install Script for Fresh Ubuntu VM
# This script automates the complete installation process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Valper AI"
VERSION="2.0.0"
DEFAULT_IP="$(hostname -I | awk '{print $1}')"

# Functions for colored output
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

log_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Header
show_header() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║                🎤 VALPER AI QUICK INSTALL 🚀                  ║"
    echo "║                                                               ║"
    echo "║           Complete Voice Assistant Setup v2.0                ║"
    echo "║                                                               ║"
    echo "║  🎯 OpenAI Whisper + TotalGPT + Kokoro TTS + React          ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Do not run this script as root!"
        log_info "Run as regular user with sudo privileges"
        exit 1
    fi
}

# Check system requirements
check_system() {
    log_header "📋 Checking System Requirements"
    
    # Check OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "OS: $PRETTY_NAME"
        
        if [[ "$ID" != "ubuntu" ]]; then
            log_warning "This script is designed for Ubuntu. Proceed with caution."
        fi
    fi
    
    # Check available memory
    TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
    log_info "Total Memory: $TOTAL_MEM"
    
    # Check available disk space
    AVAILABLE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
    log_info "Available Disk Space: $AVAILABLE_SPACE"
    
    log_success "System requirements check completed"
    echo
}

# Get user confirmation
get_confirmation() {
    log_header "🚀 Ready to Install Valper AI"
    echo
    echo "This will install and configure:"
    echo "  • 🖥️  System dependencies (Python 3.11, Node.js, Nginx)"
    echo "  • 🎤 OpenAI Whisper (Speech-to-Text)"  
    echo "  • 🔊 Kokoro TTS (Text-to-Speech)"
    echo "  • 🧠 TotalGPT API integration"
    echo "  • 🌐 React Frontend with cyberpunk UI"
    echo "  • 🔒 HTTPS/SSL configuration"
    echo "  • 🔥 Firewall setup"
    echo
    echo "Estimated time: 15-20 minutes"
    echo "Required space: ~3GB"
    echo
    
    read -p "Enter your server IP address (detected: $DEFAULT_IP): " SERVER_IP
    SERVER_IP=${SERVER_IP:-$DEFAULT_IP}
    
    echo
    while true; do
        read -p "Continue with installation? (y/n): " yn
        case $yn in
            [Yy]* ) 
                log_success "Starting installation..."
                break
                ;;
            [Nn]* ) 
                log_info "Installation cancelled"
                exit 0
                ;;
            * ) 
                echo "Please answer yes (y) or no (n)"
                ;;
        esac
    done
    echo
}

# Step 1: Install system dependencies
install_system_deps() {
    log_header "📦 Installing System Dependencies"
    
    log_step "Updating package lists..."
    sudo apt update
    
    log_step "Installing base packages..."
    sudo apt install -y curl wget git build-essential software-properties-common
    
    log_step "Adding Python 3.11 repository..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    
    log_step "Installing Python 3.11..."
    sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils python3-pip
    
    log_step "Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    
    log_step "Installing Nginx..."
    sudo apt install -y nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
    
    log_success "System dependencies installed"
    echo
}

# Step 2: Configure firewall
configure_firewall() {
    log_header "🔥 Configuring Firewall"
    
    log_step "Configuring UFW..."
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 3000/tcp
    sudo ufw allow 8000/tcp
    
    log_success "Firewall configured"
    echo
}

# Step 3: Setup virtual environments
setup_environments() {
    log_header "🏗️  Setting up Virtual Environments"
    
    # Make scripts executable
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_step "Setting up STT environment..."
    if [ -f "scripts/setup_stt_environment.sh" ]; then
        ./scripts/setup_stt_environment.sh
    else
        log_warning "STT setup script not found, skipping..."
    fi
    
    log_step "Setting up TTS environment..."
    if [ -f "scripts/setup_tts_environment.sh" ]; then
        ./scripts/setup_tts_environment.sh  
    else
        log_warning "TTS setup script not found, skipping..."
    fi
    
    log_step "Setting up Backend environment..."
    if [ -f "scripts/setup_environment.sh" ]; then
        ./scripts/setup_environment.sh
    else
        log_warning "Backend setup script not found, skipping..."
    fi
    
    log_success "Virtual environments configured"
    echo
}

# Step 4: Configure backend
configure_backend() {
    log_header "⚙️ Configuring Backend"
    
    cd backend
    
    log_step "Creating .env file..."
    cat > .env << EOF
TOTALGPT_API_KEY=sk-B-hP0huha1Z7nimfRFF69A
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
EOF
    
    log_step "Installing backend dependencies..."
    source ../venv_backend/bin/activate
    pip install -r requirements.txt
    
    cd ..
    log_success "Backend configured"
    echo
}

# Step 5: Configure frontend
configure_frontend() {
    log_header "🌐 Configuring Frontend"
    
    cd frontend
    
    log_step "Installing frontend dependencies..."
    npm install
    
    cd ..
    log_success "Frontend configured"
    echo
}

# Step 6: Setup SSL certificates
setup_ssl() {
    log_header "🔒 Setting up SSL Certificates"
    
    log_step "Creating SSL directory..."
    sudo mkdir -p /etc/ssl/valper
    
    log_step "Generating SSL certificate for IP: $SERVER_IP"
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/valper/valper.key \
        -out /etc/ssl/valper/valper.crt \
        -subj "/C=US/ST=State/L=City/O=Valper-AI/CN=$SERVER_IP" \
        -addext "subjectAltName=IP:$SERVER_IP,DNS:localhost,DNS:valper-ai.local"
    
    log_success "SSL certificates created"
    echo
}

# Step 7: Configure Nginx
configure_nginx() {
    log_header "🌍 Configuring Nginx"
    
    log_step "Creating Nginx configuration..."
    sudo tee /etc/nginx/sites-available/valper-ai > /dev/null << EOF
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
    
    log_step "Enabling Nginx site..."
    sudo ln -sf /etc/nginx/sites-available/valper-ai /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    log_step "Testing Nginx configuration..."
    sudo nginx -t
    
    log_step "Reloading Nginx..."
    sudo systemctl reload nginx
    
    log_success "Nginx configured and running"
    echo
}

# Step 8: Create startup scripts
create_startup_scripts() {
    log_header "📝 Creating Startup Scripts"
    
    log_step "Creating backend startup script..."
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

    log_step "Creating frontend startup script..."
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
echo "Cyberpunk Interface: https://$SERVER_IP (with HTTPS for microphone)"
echo "Press Ctrl+C to stop"
echo ""

exec npm start
EOF

    chmod +x scripts/start_backend.sh
    chmod +x scripts/start_frontend.sh
    
    log_success "Startup scripts created"
    echo
}

# Final verification
run_verification() {
    log_header "🧪 Running Installation Verification"
    
    # Check virtual environments
    for venv in venv_stt venv_tts venv_backend; do
        if [ -d "$venv" ]; then
            log_success "$venv environment exists"
        else
            log_warning "$venv environment missing"
        fi
    done
    
    # Check SSL certificates
    if sudo test -f "/etc/ssl/valper/valper.crt"; then
        log_success "SSL certificates exist"
    else
        log_warning "SSL certificates missing"
    fi
    
    # Check Nginx
    if sudo nginx -t &>/dev/null; then
        log_success "Nginx configuration valid"
    else
        log_warning "Nginx configuration issues"
    fi
    
    # Check firewall
    if sudo ufw status | grep -q "Status: active"; then
        log_success "Firewall is active"
    else
        log_warning "Firewall not active"
    fi
    
    echo
}

# Installation complete message
show_completion() {
    log_header "🎉 Installation Complete!"
    echo
    echo -e "${GREEN}Valper AI has been successfully installed!${NC}"
    echo
    echo "🌐 Access URLs:"
    echo "  • HTTPS: https://$SERVER_IP (recommended for microphone)"
    echo "  • HTTP:  http://$SERVER_IP"
    echo "  • API:   http://$SERVER_IP/docs"
    echo
    echo "🚀 To start Valper AI:"
    echo "  1. Terminal 1: ./scripts/start_backend.sh"
    echo "  2. Terminal 2: ./scripts/start_frontend.sh"
    echo
    echo "📋 Next Steps:"
    echo "  • Accept the SSL certificate in your browser"
    echo "  • Grant microphone permissions for voice features"
    echo "  • Test the voice conversation with the blue button"
    echo
    echo -e "${CYAN}Enjoy your Valper AI assistant! 🎤🤖${NC}"
    echo
}

# Main installation function
main() {
    show_header
    check_root
    check_system
    get_confirmation
    install_system_deps
    configure_firewall
    setup_environments
    configure_backend
    configure_frontend
    setup_ssl
    configure_nginx
    create_startup_scripts
    run_verification
    show_completion
}

# Run main function
main "$@" 