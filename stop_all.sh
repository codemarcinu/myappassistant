#!/usr/bin/env bash

set -e

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcje pomocnicze
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Funkcja zatrzymująca procesy na portach
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        log_warning "Zatrzymuję proces na porcie $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

log_info "=== FoodSave AI - Zatrzymywanie Systemu ==="

# 1. Zatrzymanie backendu przez PID
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill $BACKEND_PID 2>/dev/null; then
        log_success "Backend zatrzymany (PID: $BACKEND_PID)"
    else
        log_warning "Backend już nie działa lub nie można zatrzymać (PID: $BACKEND_PID)"
    fi
    rm -f backend.pid
else
    log_info "Plik backend.pid nie istnieje"
fi

# 2. Zatrzymanie frontendu przez PID
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill $FRONTEND_PID 2>/dev/null; then
        log_success "Frontend zatrzymany (PID: $FRONTEND_PID)"
    else
        log_warning "Frontend już nie działa lub nie można zatrzymać (PID: $FRONTEND_PID)"
    fi
    rm -f frontend.pid
else
    log_info "Plik frontend.pid nie istnieje"
fi

# 3. Dodatkowe sprawdzenie portów
log_info "Sprawdzanie zajętych portów..."

# Sprawdzenie portu 8000 (backend)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    kill_port 8000
else
    log_success "Port 8000 (backend) jest wolny"
fi

# Sprawdzenie portu 3000 (frontend)
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    kill_port 3000
else
    log_success "Port 3000 (frontend) jest wolny"
fi

# 4. Usunięcie plików logów (opcjonalne)
read -p "Czy chcesz usunąć pliki logów? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f backend.log ]; then
        rm backend.log
        log_success "Usunięto backend.log"
    fi
    if [ -f frontend.log ]; then
        rm frontend.log
        log_success "Usunięto frontend.log"
    fi
fi

echo ""
log_success "=== FoodSave AI - System Zatrzymany ==="
