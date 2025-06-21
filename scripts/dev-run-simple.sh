#!/bin/bash

# FoodSave AI - Prosty skrypt uruchamiania bez Dockera
# Maksymalna widoczność tego co się dzieje w kodzie

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

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1"
}

# Sprawdzenie wymagań
check_requirements() {
    log_step "Sprawdzanie wymagań systemowych..."

    # Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 nie jest zainstalowany"
        exit 1
    fi

    python_version=$(python3 --version | cut -d' ' -f2)
    log_success "Python $python_version - OK"

    # Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js nie jest zainstalowany"
        exit 1
    fi

    node_version=$(node --version)
    log_success "Node.js $node_version - OK"

    # npm
    if ! command -v npm &> /dev/null; then
        log_error "npm nie jest zainstalowany"
        exit 1
    fi

    npm_version=$(npm --version)
    log_success "npm $npm_version - OK"

    # Ollama (opcjonalne)
    if command -v ollama &> /dev/null; then
        log_success "Ollama - OK (opcjonalne)"
    else
        log_warning "Ollama nie jest zainstalowane - niektóre funkcje AI mogą nie działać"
    fi

    # Redis (opcjonalne)
    if command -v redis-server &> /dev/null; then
        log_success "Redis - OK (opcjonalne)"
    else
        log_warning "Redis nie jest zainstalowane - cache będzie wyłączone"
    fi
}

# Tworzenie katalogów
create_directories() {
    log_step "Tworzenie katalogów..."

    mkdir -p data
    mkdir -p logs/{backend,frontend}
    mkdir -p backups/{config,database,files,vector_store}

    log_success "Katalogi utworzone"
}

# Sprawdzenie pliku .env
check_env() {
    log_step "Sprawdzanie konfiguracji..."

    if [ ! -f ".env" ]; then
        if [ -f "env.dev.example" ]; then
            log_info "Kopiuję env.dev.example do .env..."
            cp env.dev.example .env
            log_success "Utworzono .env z szablonu"
            log_warning "Edytuj .env i dostosuj wartości do swojego środowiska"
        else
            log_warning "Brak pliku .env - używam domyślnych ustawień"
        fi
    else
        log_success "Plik .env istnieje"
    fi
}

# Instalacja zależności backend
install_backend_deps() {
    log_step "Instalacja zależności backend..."

    # Sprawdzenie czy jesteśmy w katalogu głównym czy scripts
    if [ -d "src/backend" ]; then
        cd src/backend
    elif [ -d "../src/backend" ]; then
        cd ../src/backend
    else
        log_error "Nie można znaleźć katalogu src/backend"
        exit 1
    fi

    log_info "Instalacja zależności przez pip..."

    # Sprawdzenie czy plik requirements-fix.txt istnieje i nie jest pusty
    if [ -f "requirements-fix.txt" ] && [ -s "requirements-fix.txt" ]; then
        log_info "Używam requirements-fix.txt z katalogu backend..."
        pip3 install -r requirements-fix.txt
    elif [ -f "../../requirements-fix.txt" ]; then
        log_info "Używam requirements-fix.txt z katalogu głównego..."
        pip3 install -r ../../requirements-fix.txt
    else
        log_error "Brak pliku requirements-fix.txt"
        exit 1
    fi

    # Powrót do katalogu głównego
    if [ -d "../../src/backend" ]; then
        cd ../..
    else
        cd ../..
    fi
    log_success "Zależności backend zainstalowane"
}

# Instalacja zależności frontend
install_frontend_deps() {
    log_step "Instalacja zależności frontend..."

    # Sprawdzenie czy jesteśmy w katalogu głównym czy scripts
    if [ -d "foodsave-frontend" ]; then
        cd foodsave-frontend
    elif [ -d "../foodsave-frontend" ]; then
        cd ../foodsave-frontend
    else
        log_error "Nie można znaleźć katalogu foodsave-frontend"
        exit 1
    fi

    if [ ! -d "node_modules" ]; then
        log_info "Instalacja npm packages..."
        npm install
    else
        log_info "node_modules istnieje - pomijam instalację"
    fi

    # Powrót do katalogu głównego
    if [ -d "../foodsave-frontend" ]; then
        cd ..
    else
        cd ..
    fi
    log_success "Zależności frontend zainstalowane"
}

# Uruchomienie Redis (jeśli dostępny)
start_redis() {
    if command -v redis-server &> /dev/null; then
        log_step "Uruchamianie Redis..."

        # Sprawdzenie czy Redis już działa
        if ! pgrep -x "redis-server" > /dev/null; then
            log_info "Uruchamianie Redis w tle..."
            redis-server --daemonize yes --port 6379
            sleep 2
            log_success "Redis uruchomiony"
        else
            log_success "Redis już działa"
        fi
    else
        log_warning "Redis nie jest zainstalowane - pomijam"
    fi
}

# Uruchomienie Ollama (jeśli dostępne)
start_ollama() {
    if command -v ollama &> /dev/null; then
        log_step "Sprawdzanie Ollama..."

        # Sprawdzenie czy Ollama działa
        if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
            log_success "Ollama już działa"
        else
            log_info "Uruchamianie Ollama w tle..."
            ollama serve &
            sleep 3
            log_success "Ollama uruchomione"
        fi
    else
        log_warning "Ollama nie jest zainstalowane - pomijam"
    fi
}

# Uruchomienie backend
start_backend() {
    log_step "Uruchamianie backend (FastAPI)..."

    # Sprawdzenie czy jesteśmy w katalogu głównym czy scripts
    if [ -d "src/backend" ]; then
        cd src/backend
    elif [ -d "../src/backend" ]; then
        cd ../src/backend
    else
        log_error "Nie można znaleźć katalogu src/backend"
        exit 1
    fi

    # Ustawienie zmiennych środowiskowych dla development
    export ENVIRONMENT=development
    export LOG_LEVEL=DEBUG
    export PYTHONPATH="${PWD}"

    log_info "Uruchamianie z maksymalnym logowaniem..."
    log_info "Endpointy będą dostępne na:"
    log_info "  - API: http://localhost:8000"
    log_info "  - Docs: http://localhost:8000/docs"
    log_info "  - Health: http://localhost:8000/health"

    # Uruchomienie z uvicorn w trybie reload
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug --reload --reload-dir . &
    BACKEND_PID=$!
    cd ../..

    # Czekanie na uruchomienie backend
    log_info "Czekanie na uruchomienie backend..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend uruchomiony (PID: $BACKEND_PID)"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            log_error "Backend nie uruchomił się w ciągu 30 sekund"
            exit 1
        fi
    done
}

# Uruchomienie frontend
start_frontend() {
    log_step "Uruchamianie frontend (Next.js)..."

    # Sprawdzenie czy jesteśmy w katalogu głównym czy scripts
    if [ -d "foodsave-frontend" ]; then
        cd foodsave-frontend
    elif [ -d "../foodsave-frontend" ]; then
        cd ../foodsave-frontend
    else
        log_error "Nie można znaleźć katalogu foodsave-frontend"
        exit 1
    fi

    # Tworzenie katalogu logów dla frontendu
    mkdir -p ../../logs/frontend

    log_info "Uruchamianie w trybie development..."
    log_info "Frontend będzie dostępny na: http://localhost:3000"
    log_info "Logi frontendu będą zapisywane w: logs/frontend/frontend.log"

    # Uruchomienie Next.js w trybie development z logowaniem do pliku
    npm run dev > ../../logs/frontend/frontend.log 2>&1 &
    FRONTEND_PID=$!

    # Powrót do katalogu głównego
    if [ -d "../foodsave-frontend" ]; then
        cd ..
    else
        cd ..
    fi

    # Czekanie na uruchomienie frontend
    log_info "Czekanie na uruchomienie frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            log_success "Frontend uruchomiony (PID: $FRONTEND_PID)"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            log_error "Frontend nie uruchomił się w ciągu 30 sekund"
            exit 1
        fi
    done
}

# Wyświetlenie statusu
show_status() {
    log_step "Status aplikacji:"

    echo ""
    log_info "🌐 Frontend:     http://localhost:3000"
    log_info "🔧 Backend API:  http://localhost:8000"
    log_info "📊 API Docs:     http://localhost:8000/docs"
    log_info "🏥 Health Check: http://localhost:8000/health"
    log_info "📈 Metrics:      http://localhost:8000/metrics"
    log_info "📋 Monitor Logów: http://localhost:8000/logs-monitor.html"

    if command -v ollama &> /dev/null; then
        log_info "🤖 Ollama:       http://localhost:11434"
    fi

    if command -v redis-server &> /dev/null; then
        log_info "🗄️  Redis:        localhost:6379"
    fi

    echo ""
    log_info "Procesy:"
    log_info "  Backend PID:  $BACKEND_PID"
    log_info "  Frontend PID: $FRONTEND_PID"

    echo ""
    log_info "Logi są zapisywane w katalogu logs/"
    log_info "Aby zatrzymać aplikację, naciśnij Ctrl+C"

    # Otwórz monitor logów w przeglądarce
    open_logs_monitor
}

# Otwieranie monitora logów w przeglądarce
open_logs_monitor() {
    log_step "Otwieranie monitora logów w przeglądarce..."

    # Czekanie na uruchomienie backend
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Sprawdzenie czy backend działa
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        # Kopiowanie pliku monitora logów do katalogu backend
        if [ -f "logs-monitor.html" ]; then
            cp logs-monitor.html src/backend/
            log_success "Monitor logów skopiowany do backend"
        fi

        # Otwieranie w przeglądarce
        if command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:8000/logs-monitor.html" &
        elif command -v open &> /dev/null; then
            open "http://localhost:8000/logs-monitor.html" &
        elif command -v sensible-browser &> /dev/null; then
            sensible-browser "http://localhost:8000/logs-monitor.html" &
        else
            log_warning "Nie można automatycznie otworzyć przeglądarki"
            log_info "Otwórz ręcznie: http://localhost:8000/logs-monitor.html"
        fi
    else
        log_warning "Backend nie jest jeszcze gotowy - monitor logów zostanie otwarty później"
    fi
}

# Funkcja cleanup
cleanup() {
    log_step "Zatrzymywanie aplikacji..."

    if [ ! -z "$BACKEND_PID" ]; then
        log_info "Zatrzymywanie backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        log_info "Zatrzymywanie frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    log_success "Aplikacja zatrzymana"
    exit 0
}

# Trap dla Ctrl+C
trap cleanup SIGINT SIGTERM

# Funkcja zapewniająca środowisko venv
ensure_venv() {
    log_step "Sprawdzanie środowiska wirtualnego (venv)..."
    if [ ! -d "../venv" ] && [ ! -d "venv" ]; then
        log_info "Tworzę środowisko venv w katalogu głównym..."
        cd ..
        python3 -m venv venv
        cd scripts
        log_success "Utworzono venv."
    else
        log_info "venv już istnieje."
    fi
    # Aktywacja venv
    if [ -f "../venv/bin/activate" ]; then
        log_info "Aktywuję venv..."
        # shellcheck disable=SC1091
        source ../venv/bin/activate
        log_success "venv aktywowane."
    elif [ -f "venv/bin/activate" ]; then
        log_info "Aktywuję venv..."
        # shellcheck disable=SC1091
        source venv/bin/activate
        log_success "venv aktywowane."
    else
        log_error "Nie znaleziono pliku aktywującego venv!"
        exit 1
    fi
}

# Główna funkcja
main() {
    echo "🚀 FoodSave AI - Uruchamianie bez Dockera"
    echo "=========================================="

    ensure_venv
    check_requirements
    create_directories
    check_env
    install_backend_deps
    install_frontend_deps
    start_redis
    start_ollama
    start_backend
    start_frontend
    show_status

    log_success "Aplikacja uruchomiona pomyślnie!"
    log_info "Naciśnij Ctrl+C aby zatrzymać"

    # Czekanie na zakończenie
    wait
}

# Uruchomienie głównej funkcji
main
