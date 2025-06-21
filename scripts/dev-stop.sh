#!/bin/bash

# FoodSave AI - Skrypt zatrzymywania aplikacji bez Dockera

set -e

# Kolory dla output
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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Funkcja zatrzymywania procesów
stop_processes() {
    log_info "Zatrzymywanie procesów FoodSave AI..."

    # Zatrzymanie procesów Python (backend)
    pids=$(pgrep -f "uvicorn.*main:app" || true)
    if [ ! -z "$pids" ]; then
        log_info "Zatrzymywanie backend procesów: $pids"
        echo $pids | xargs kill -TERM
        sleep 2
        # Sprawdzenie czy procesy zostały zatrzymane
        remaining=$(pgrep -f "uvicorn.*main:app" || true)
        if [ ! -z "$remaining" ]; then
            log_warning "Procesy backend nie zatrzymały się, wymuszam..."
            echo $remaining | xargs kill -KILL
        fi
        log_success "Backend zatrzymany"
    else
        log_info "Brak uruchomionych procesów backend"
    fi

    # Zatrzymanie procesów Node.js (frontend)
    pids=$(pgrep -f "next dev" || true)
    if [ ! -z "$pids" ]; then
        log_info "Zatrzymywanie frontend procesów: $pids"
        echo $pids | xargs kill -TERM
        sleep 2
        # Sprawdzenie czy procesy zostały zatrzymane
        remaining=$(pgrep -f "next dev" || true)
        if [ ! -z "$remaining" ]; then
            log_warning "Procesy frontend nie zatrzymały się, wymuszam..."
            echo $remaining | xargs kill -KILL
        fi
        log_success "Frontend zatrzymany"
    else
        log_info "Brak uruchomionych procesów frontend"
    fi
}

# Funkcja zatrzymywania Redis (jeśli uruchomiony przez skrypt)
stop_redis() {
    if command -v redis-server &> /dev/null; then
        log_info "Sprawdzanie Redis..."
        if pgrep -x "redis-server" > /dev/null; then
            log_info "Zatrzymywanie Redis..."
            redis-cli shutdown || true
            log_success "Redis zatrzymany"
        else
            log_info "Redis nie był uruchomiony przez skrypt"
        fi
    fi
}

# Funkcja zatrzymywania Ollama (jeśli uruchomione przez skrypt)
stop_ollama() {
    if command -v ollama &> /dev/null; then
        log_info "Sprawdzanie Ollama..."
        # Sprawdzenie czy Ollama działa
        if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
            log_info "Ollama działa - zostawiam uruchomione (może być używane przez inne aplikacje)"
        else
            log_info "Ollama nie działa"
        fi
    fi
}

# Funkcja sprawdzania portów
check_ports() {
    log_info "Sprawdzanie portów..."

    # Sprawdzenie portu 8000 (backend)
    if lsof -i :8000 > /dev/null 2>&1; then
        log_warning "Port 8000 (backend) jest nadal zajęty"
    else
        log_success "Port 8000 (backend) jest wolny"
    fi

    # Sprawdzenie portu 3000 (frontend)
    if lsof -i :3000 > /dev/null 2>&1; then
        log_warning "Port 3000 (frontend) jest nadal zajęty"
    else
        log_success "Port 3000 (frontend) jest wolny"
    fi
}

# Główna funkcja
main() {
    echo "🛑 FoodSave AI - Zatrzymywanie aplikacji"
    echo "========================================"

    stop_processes
    stop_redis
    stop_ollama
    check_ports

    log_success "Aplikacja FoodSave AI została zatrzymana"
}

# Uruchomienie głównej funkcji
main
