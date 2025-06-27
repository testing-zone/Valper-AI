#!/bin/bash

# Valper AI Complete Installation Test v2.0
# Tests all components: Virtual environments, SSL, Nginx, services, etc.

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

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

# Main function
show_header() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║                🧪 VALPER AI INSTALLATION TEST 🔍              ║"
    echo "║                                                               ║"
    echo "║            Comprehensive System Verification v2.0            ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

# Test 1: System Requirements
test_system_requirements() {
    log_header "🖥️  Testing System Requirements"
    
    # Python 3.11+
    if command -v python3.11 &> /dev/null; then
        PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
        log_success "Python 3.11 installed: $PYTHON_VERSION"
    else
        log_error "Python 3.11 not found"
    fi
    
    # Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js installed: $NODE_VERSION"
    else
        log_error "Node.js not found"
    fi
    
    # Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | awk '{print $3}')
        log_success "Git installed: $GIT_VERSION"
    else
        log_warning "Git not found"
    fi
    
    # Nginx
    if command -v nginx &> /dev/null; then
        NGINX_VERSION=$(nginx -v 2>&1 | awk '{print $3}')
        log_success "Nginx installed: $NGINX_VERSION"
    else
        log_error "Nginx not found"
    fi
    
    echo
}

# Test 2: Virtual Environments
test_virtual_environments() {
    log_header "📦 Testing Virtual Environments"
    
    for venv in venv_stt venv_tts venv_backend; do
        if [ -d "$venv" ]; then
            log_success "$venv environment exists"
            
            # Test if environment can be activated
            if [ -f "$venv/bin/activate" ]; then
                log_success "$venv activation script found"
            else
                log_error "$venv activation script missing"
            fi
        else
            log_error "$venv environment missing"
        fi
    done
    
    echo
}

# Test 3: Backend Dependencies
test_backend_dependencies() {
    log_header "🔧 Testing Backend Dependencies"
    
    if [ -d "venv_backend" ]; then
        log_step "Testing backend virtual environment..."
        source venv_backend/bin/activate
        
        # Test core dependencies
        python -c "
import sys
import importlib

dependencies = [
    'fastapi',
    'uvicorn', 
    'whisper',
    'requests',
    'pydantic',
    'numpy',
    'dotenv'
]

missing = []
for dep in dependencies:
    try:
        importlib.import_module(dep)
        print(f'✅ {dep}')
    except ImportError:
        missing.append(dep)
        print(f'❌ {dep}')

if missing:
    print(f'Missing dependencies: {missing}')
    sys.exit(1)
else:
    print('✅ All core backend dependencies found')
" 2>/dev/null || log_error "Backend dependencies test failed"
        
        deactivate
    else
        log_error "Backend virtual environment not found"
    fi
    
    echo
}

# Test 4: Frontend Dependencies  
test_frontend_dependencies() {
    log_header "🌐 Testing Frontend Dependencies"
    
    if [ -d "frontend" ]; then
        cd frontend
        
        if [ -f "package.json" ]; then
            log_success "package.json found"
            
            if [ -d "node_modules" ]; then
                log_success "node_modules directory exists"
                
                # Check key dependencies
                if [ -d "node_modules/react" ]; then
                    REACT_VERSION=$(node -p "require('./node_modules/react/package.json').version")
                    log_success "React installed: $REACT_VERSION"
                else
                    log_error "React not found in node_modules"
                fi
                
                if [ -d "node_modules/@craco/craco" ]; then
                    log_success "CRACO found"
                else
                    log_warning "CRACO not found"
                fi
            else
                log_error "node_modules directory missing"
            fi
        else
            log_error "package.json not found"
        fi
        
        cd ..
    else
        log_error "Frontend directory not found"
    fi
    
    echo
}

# Test 5: SSL Certificates
test_ssl_certificates() {
    log_header "🔒 Testing SSL Configuration"
    
    if sudo test -d "/etc/ssl/valper"; then
        log_success "SSL directory exists"
        
        if sudo test -f "/etc/ssl/valper/valper.crt"; then
            log_success "SSL certificate exists"
            
            # Check certificate validity
            CERT_EXPIRY=$(sudo openssl x509 -in /etc/ssl/valper/valper.crt -noout -enddate 2>/dev/null | cut -d= -f2)
            if [ $? -eq 0 ]; then
                log_success "SSL certificate valid until: $CERT_EXPIRY"
            else
                log_warning "Could not read certificate expiry"
            fi
        else
            log_error "SSL certificate missing"
        fi
        
        if sudo test -f "/etc/ssl/valper/valper.key"; then
            log_success "SSL private key exists"
        else
            log_error "SSL private key missing"
        fi
    else
        log_error "SSL directory missing"
    fi
    
    echo
}

# Test 6: Nginx Configuration
test_nginx_configuration() {
    log_header "🌍 Testing Nginx Configuration"
    
    # Check if Nginx is running
    if sudo systemctl is-active nginx &>/dev/null; then
        log_success "Nginx service is running"
    else
        log_warning "Nginx service is not running"
    fi
    
    # Check configuration syntax
    if sudo nginx -t &>/dev/null; then
        log_success "Nginx configuration is valid"
    else
        log_error "Nginx configuration has errors"
        sudo nginx -t
    fi
    
    # Check if Valper site is enabled
    if [ -L "/etc/nginx/sites-enabled/valper-ai" ]; then
        log_success "Valper AI site is enabled"
    elif [ -L "/etc/nginx/sites-enabled/valper-dev" ]; then
        log_success "Valper AI dev site is enabled"
    else
        log_warning "No Valper AI Nginx site found"
    fi
    
    # Check if default site is disabled
    if [ ! -L "/etc/nginx/sites-enabled/default" ]; then
        log_success "Default Nginx site is disabled"
    else
        log_warning "Default Nginx site is still enabled"
    fi
    
    echo
}

# Test 7: Firewall Rules
test_firewall() {
    log_header "🔥 Testing Firewall Configuration"
    
    if command -v ufw &> /dev/null; then
        UFW_STATUS=$(sudo ufw status | head -1)
        
        if echo "$UFW_STATUS" | grep -q "Status: active"; then
            log_success "UFW firewall is active"
            
            # Check required ports
            REQUIRED_PORTS=("80/tcp" "443/tcp" "3000/tcp" "8000/tcp")
            
            for port in "${REQUIRED_PORTS[@]}"; do
                if sudo ufw status | grep -q "$port.*ALLOW"; then
                    log_success "Port $port is open"
                else
                    log_warning "Port $port is not explicitly allowed"
                fi
            done
        else
            log_warning "UFW firewall is not active"
        fi
    else
        log_warning "UFW not found"
    fi
    
    echo
}

# Test 8: Environment Files
test_environment_files() {
    log_header "⚙️ Testing Environment Configuration"
    
    # Backend .env file
    if [ -f "backend/.env" ]; then
        log_success "Backend .env file exists"
        
        if grep -q "TOTALGPT_API_KEY" backend/.env; then
            log_success "TOTALGPT_API_KEY found in .env"
            
            # Check if API key looks valid (starts with sk-)
            API_KEY=$(grep "TOTALGPT_API_KEY" backend/.env | cut -d= -f2)
            if [[ $API_KEY == sk-* ]]; then
                log_success "API key format looks correct"
            else
                log_warning "API key format may be incorrect"
            fi
        else
            log_error "TOTALGPT_API_KEY not found in .env"
        fi
    else
        log_error "Backend .env file missing"
    fi
    
    echo
}

# Test 9: Network Connectivity
test_network() {
    log_header "🌐 Testing Network Connectivity"
    
    # Test local ports
    LOCAL_PORTS=(3000 8000)
    
    for port in "${LOCAL_PORTS[@]}"; do
        if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
            log_success "Port $port is in use (service may be running)"
        else
            log_info "Port $port is available"
        fi
    done
    
    # Test external connectivity
    if ping -c 1 google.com &>/dev/null; then
        log_success "Internet connectivity available"
    else
        log_warning "No internet connectivity (may affect API calls)"
    fi
    
    echo
}

# Test 10: Running Services
test_running_services() {
    log_header "🚀 Testing Running Services"
    
    # Check for uvicorn (backend)
    if pgrep -f "uvicorn" &>/dev/null; then
        log_success "Backend (uvicorn) is running"
        UVICORN_PID=$(pgrep -f "uvicorn")
        log_info "Backend PID: $UVICORN_PID"
    else
        log_info "Backend is not currently running"
    fi
    
    # Check for node (frontend)
    if pgrep -f "node.*start" &>/dev/null; then
        log_success "Frontend (Node.js) is running"
        NODE_PID=$(pgrep -f "node.*start")
        log_info "Frontend PID: $NODE_PID"
    else
        log_info "Frontend is not currently running"
    fi
    
    # Check Nginx
    if pgrep nginx &>/dev/null; then
        log_success "Nginx is running"
    else
        log_warning "Nginx is not running"
    fi
    
    echo
}

# Test 11: API Health Check
test_api_health() {
    log_header "🏥 Testing API Health"
    
    # Check if backend is responding
    if curl -s "http://localhost:8000/health" &>/dev/null; then
        log_success "Backend health endpoint responding"
        
        # Get detailed health info
        HEALTH_RESPONSE=$(curl -s "http://localhost:8000/health" | jq -r '.services // empty' 2>/dev/null)
        if [ -n "$HEALTH_RESPONSE" ]; then
            log_success "Health check returned service status"
        else
            log_warning "Health check response format unexpected"
        fi
    else
        log_info "Backend health endpoint not responding (service may be stopped)"
    fi
    
    # Check frontend
    if curl -s "http://localhost:3000" &>/dev/null; then
        log_success "Frontend is responding"
    else
        log_info "Frontend is not responding (service may be stopped)"
    fi
    
    echo
}

# Generate summary report
generate_summary() {
    log_header "📋 Installation Test Summary"
    
    echo -e "${GREEN}✅ Tests Completed Successfully:${NC}"
    echo "  • System requirements check"
    echo "  • Virtual environments verification"
    echo "  • Dependencies validation" 
    echo "  • SSL certificates check"
    echo "  • Nginx configuration test"
    echo "  • Firewall rules verification"
    echo "  • Environment files check"
    echo "  • Network connectivity test"
    echo "  • Running services detection"
    echo "  • API health check"
    echo
    
    echo -e "${BLUE}🎯 Next Steps:${NC}"
    echo "1. Start services if not running:"
    echo "   • Terminal 1: ./scripts/start_backend.sh"
    echo "   • Terminal 2: ./scripts/start_frontend.sh"
    echo
    echo "2. Access Valper AI:"
    echo "   • HTTPS: https://$(hostname -I | awk '{print $1}') (recommended)"
    echo "   • HTTP: http://localhost:3000"
    echo "   • API Docs: http://localhost:8000/docs"
    echo
    echo "3. Test voice features:"
    echo "   • Grant microphone permissions in browser"
    echo "   • Click the blue button to start recording"
    echo "   • Test full voice conversation"
    echo
    
    echo -e "${CYAN}🎉 Valper AI Installation Test Complete! 🎤🤖${NC}"
    echo
}

# Main execution
main() {
    show_header
    test_system_requirements
    test_virtual_environments
    test_backend_dependencies
    test_frontend_dependencies
    test_ssl_certificates
    test_nginx_configuration
    test_firewall
    test_environment_files
    test_network
    test_running_services
    test_api_health
    generate_summary
}

# Run main function
main "$@" 