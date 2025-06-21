#!/bin/bash

# FoodSave AI - Skrypt sprawdzania statusu aplikacji bez Dockera

set -e

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funkcje pomocnicze
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Sprawdzenie procesów
check_processes() {
    log_step "Sprawdzanie procesów aplikacji..."

    # Backend (Python/FastAPI)
    backend_pids=$(pgrep -f "uvicorn.*main:app" || true)
    if [ ! -z "$backend_pids" ]; then
        log_success "Backend działa (PID: $backend_pids)"
    else
        log_error "Backend nie działa"
    fi

    # Frontend (Next.js)
    frontend_pids=$(pgrep -f "next dev" || true)
    if [ ! -z "$frontend_pids" ]; then
        log_success "Frontend działa (PID: $frontend_pids)"
    else
        log_error "Frontend nie działa"
    fi
}

# Sprawdzenie portów
check_ports() {
    log_step "Sprawdzanie portów..."

    # Port 8000 (Backend)
    if lsof -i :8000 > /dev/null 2>&1; then
        log_success "Port 8000 (Backend) - OK"
    else
        log_error "Port 8000 (Backend) - NIE DZIAŁA"
    fi

    # Port 3000 (Frontend)
    if lsof -i :3000 > /dev/null 2>&1; then
        log_success "Port 3000 (Frontend) - OK"
    else
        log_error "Port 3000 (Frontend) - NIE DZIAŁA"
    fi

    # Port 11434 (Ollama)
    if lsof -i :11434 > /dev/null 2>&1; then
        log_success "Port 11434 (Ollama) - OK"
    else
        log_warning "Port 11434 (Ollama) - NIE DZIAŁA"
    fi

    # Port 6379 (Redis)
    if lsof -i :6379 > /dev/null 2>&1; then
        log_success "Port 6379 (Redis) - OK"
    else
        log_warning "Port 6379 (Redis) - NIE DZIAŁA"
    fi
}

# Sprawdzenie endpointów HTTP
check_endpoints() {
    log_step "Sprawdzanie endpointów HTTP..."

    # Backend Health
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend Health - OK"
    else
        log_error "Backend Health - NIE DZIAŁA"
    fi

    # Frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend - OK"
    else
        log_error "Frontend - NIE DZIAŁA"
    fi

    # Ollama
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        log_success "Ollama API - OK"
    else
        log_warning "Ollama API - NIE DZIAŁA"
    fi

    # Redis
    if command -v redis-cli > /dev/null 2>&1; then
        if redis-cli ping > /dev/null 2>&1; then
            log_success "Redis - OK"
        else
            log_warning "Redis - NIE DZIAŁA"
        fi
    else
        log_warning "Redis CLI nie jest zainstalowane"
    fi
}

# Sprawdzenie użycia zasobów
check_resources() {
    log_step "Sprawdzanie użycia zasobów..."

    # Backend
    backend_pids=$(pgrep -f "uvicorn.*main:app" || true)
    if [ ! -z "$backend_pids" ]; then
        backend_mem=$(ps -o rss= -p $backend_pids | awk '{sum+=$1} END {print sum/1024 " MB"}')
        log_info "Backend używa pamięci: $backend_mem"
    fi

    # Frontend
    frontend_pids=$(pgrep -f "next dev" || true)
    if [ ! -z "$frontend_pids" ]; then
        frontend_mem=$(ps -o rss= -p $frontend_pids | awk '{sum+=$1} END {print sum/1024 " MB"}')
        log_info "Frontend używa pamięci: $frontend_mem"
    fi

    # Ogólne użycie systemu
    total_mem=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    log_info "Ogólne użycie pamięci systemu: $total_mem"

    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    log_info "Użycie CPU: ${cpu_usage}%"
}

# Sprawdzenie logów
check_logs() {
    log_step "Sprawdzanie logów..."

    if [ -d "logs" ]; then
        log_info "Katalog logów istnieje"

        # Sprawdzenie ostatnich logów backend
        if [ -f "logs/backend/backend.log" ]; then
            last_backend_log=$(tail -1 logs/backend/backend.log 2>/dev/null || echo "Brak logów")
            log_info "Ostatni log backend: $last_backend_log"
        fi

        # Sprawdzenie ostatnich logów frontend
        if [ -f "logs/frontend/frontend.log" ]; then
            last_frontend_log=$(tail -1 logs/frontend/frontend.log 2>/dev/null || echo "Brak logów")
            log_info "Ostatni log frontend: $last_frontend_log"
        fi
    else
        log_warning "Katalog logów nie istnieje"
    fi
}

# Wyświetlenie linków
show_links() {
    log_step "Dostępne linki:"

    echo ""
    log_info "🌐 Frontend:     http://localhost:3000"
    log_info "🔧 Backend API:  http://localhost:8000"
    log_info "📊 API Docs:     http://localhost:8000/docs"
    log_info "🏥 Health Check: http://localhost:8000/health"
    log_info "📈 Metrics:      http://localhost:8000/metrics"
    log_info "📋 Status:       http://localhost:8000/api/v1/status"

    if lsof -i :11434 > /dev/null 2>&1; then
        log_info "🤖 Ollama:       http://localhost:11434"
    fi

    if lsof -i :6379 > /dev/null 2>&1; then
        log_info "🗄️  Redis:        localhost:6379"
    fi
}

# Główna funkcja
main() {
    echo "📊 FoodSave AI - Status aplikacji"
    echo "=================================="

    check_processes
    check_ports
    check_endpoints
    check_resources
    check_logs
    show_links

    echo ""
    log_info "Aby uruchomić aplikację: ./scripts/dev-run-simple.sh"
    log_info "Aby zatrzymać aplikację: ./scripts/dev-stop.sh"
}

# Uruchomienie głównej funkcji
main
