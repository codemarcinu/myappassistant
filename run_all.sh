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

# Funkcja sprawdzająca czy port jest zajęty
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
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

# Funkcja sprawdzająca czy plik istnieje
check_file() {
    if [ ! -f "$1" ]; then
        log_error "Plik $1 nie istnieje!"
        return 1
    fi
    return 0
}

# Funkcja sprawdzająca czy katalog istnieje
check_dir() {
    if [ ! -d "$1" ]; then
        log_error "Katalog $1 nie istnieje!"
        return 1
    fi
    return 0
}

# Funkcja sprawdzająca czy komenda jest dostępna
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "Komenda $1 nie jest dostępna!"
        return 1
    fi
    return 0
}

log_info "=== FoodSave AI - Uruchamianie Systemu ==="

# 1. Sprawdzenie podstawowych wymagań
log_info "Sprawdzanie podstawowych wymagań..."

# Sprawdzenie Python
if ! check_command python3; then
    log_error "Python 3 nie jest zainstalowany!"
    exit 1
fi

# Sprawdzenie Node.js
if ! check_command node; then
    log_error "Node.js nie jest zainstalowany!"
    exit 1
fi

# Sprawdzenie npm
if ! check_command npm; then
    log_error "npm nie jest zainstalowany!"
    exit 1
fi

# Sprawdzenie Poetry
if ! check_command poetry; then
    log_error "Poetry nie jest zainstalowany!"
    exit 1
fi

log_success "Podstawowe wymagania spełnione"

# 2. Sprawdzenie połączenia internetowego
log_info "Sprawdzanie połączenia internetowego..."
if curl -s --head https://google.com | grep '200 OK' > /dev/null; then
    log_success "Połączenie internetowe działa"
else
    log_warning "Brak połączenia z internetem - niektóre funkcje mogą nie działać"
fi

# 3. Sprawdzenie Ollama
log_info "Sprawdzanie Ollama..."
if curl -s http://localhost:11434/api/tags | grep -q 'models' 2>/dev/null; then
    log_success "Ollama działa"
    # Wypisanie dostępnych modeli
    MODELS=$(curl -s http://localhost:11434/api/tags | grep 'name' | cut -d '"' -f4 2>/dev/null || echo "brak modeli")
    log_info "Dostępne modele Ollama: $MODELS"
else
    log_warning "Ollama nie działa na porcie 11434 - uruchom: ollama serve"
fi

# 4. Sprawdzenie struktury projektu
log_info "Sprawdzanie struktury projektu..."

# Sprawdzenie głównych katalogów
check_dir "src/backend" || exit 1
check_dir "foodsave-frontend" || exit 1
check_dir "venv" || exit 1

# Sprawdzenie głównych plików
check_file "pyproject.toml" || exit 1
check_file "foodsave-frontend/package.json" || exit 1
check_file ".env" || log_warning "Plik .env nie istnieje - utworzę domyślny"

log_success "Struktura projektu poprawna"

# 5. Sprawdzenie i utworzenie pliku .env jeśli nie istnieje
if [ ! -f ".env" ]; then
    log_info "Tworzenie domyślnego pliku .env..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=sqlite:///./foodsave.db

# API Keys (opcjonalne - aplikacja będzie działać bez nich)
NEWS_API_KEY=your_news_api_key_here
BING_SEARCH_API_KEY=your_bing_search_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
EOF
    log_success "Utworzono domyślny plik .env"
fi

# 6. Sprawdzenie zależności Python
log_info "Sprawdzanie zależności Python..."
if [ ! -d "venv" ]; then
    log_info "Tworzenie wirtualnego środowiska..."
    python3 -m venv venv
fi

# Aktywacja venv
source venv/bin/activate

# Sprawdzenie czy Poetry dependencies są zainstalowane
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    log_info "Instalowanie zależności Python..."
    poetry install --no-dev
fi

log_success "Zależności Python sprawdzone"

# 7. Sprawdzenie zależności Node.js
log_info "Sprawdzanie zależności Node.js..."
cd foodsave-frontend

if [ ! -d "node_modules" ]; then
    log_info "Instalowanie zależności Node.js..."
    npm install
fi

cd ..
log_success "Zależności Node.js sprawdzone"

# 8. Zatrzymanie istniejących procesów na portach
log_info "Sprawdzanie zajętych portów..."
kill_port 8000
kill_port 3000

# 9. Uruchomienie backendu
log_info "Uruchamianie backendu (FastAPI)..."

# Sprawdzenie czy main.py istnieje
if [ ! -f "src/backend/main.py" ]; then
    log_error "Plik main.py nie istnieje w src/backend/"
    exit 1
fi

# Uruchomienie backendu w tle z głównego katalogu projektu
nohup uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

# Czekanie na uruchomienie backendu
sleep 3

# Sprawdzenie czy backend się uruchomił
if ! ps -p $BACKEND_PID > /dev/null; then
    log_error "Backend nie uruchomił się! Sprawdź backend.log"
    exit 1
fi

# Nowa logika oczekiwania na HTTP
MAX_WAIT=20
WAITED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1 && ! curl -s http://localhost:8000/ > /dev/null 2>&1; do
    if ! ps -p $BACKEND_PID > /dev/null; then
        log_error "Backend nie uruchomił się! Sprawdź backend.log"
        exit 1
    fi
    if [ $WAITED -ge $MAX_WAIT ]; then
        log_warning "Backend uruchomiony ale nie odpowiada na HTTP po $MAX_WAIT sekundach (PID: $BACKEND_PID)"
        break
    fi
    if [ $WAITED -eq 0 ]; then
        log_info "Backend startuje, czekam na HTTP (do $MAX_WAIT sekund)..."
    fi
    sleep 1
    WAITED=$((WAITED+1))
done

if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/ > /dev/null 2>&1; then
    log_success "Backend uruchomiony i odpowiada na HTTP (PID: $BACKEND_PID)"
fi

# 10. Uruchomienie frontendu
log_info "Uruchamianie frontendu (Next.js)..."
cd foodsave-frontend

# Uruchomienie frontendu w tle
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

cd ..

# Czekanie na uruchomienie frontendu
sleep 5

# Sprawdzenie czy frontend się uruchomił
if ! ps -p $FRONTEND_PID > /dev/null; then
    log_error "Frontend nie uruchomił się! Sprawdź frontend.log"
    exit 1
fi

# Sprawdzenie czy frontend odpowiada
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    log_success "Frontend uruchomiony (PID: $FRONTEND_PID)"
    # Otwórz przeglądarkę z aplikacją
    xdg-open http://localhost:3000 > /dev/null 2>&1 &
else
    log_warning "Frontend uruchomiony ale nie odpowiada na HTTP (PID: $FRONTEND_PID)"
fi

# 11. Finalne sprawdzenie
log_info "Sprawdzanie statusu aplikacji..."
sleep 2

echo ""
log_success "=== FoodSave AI - System Uruchomiony ==="
echo ""
echo -e "${GREEN}Backend:${NC}  http://localhost:8000 (PID: $BACKEND_PID)"
echo -e "${GREEN}Frontend:${NC} http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo -e "${BLUE}Logi:${NC}"
echo -e "  Backend:  backend.log"
echo -e "  Frontend: frontend.log"
echo ""
echo -e "${YELLOW}Aby zatrzymać aplikację, uruchom:${NC} ./stop_all.sh"
echo ""

# Sprawdzenie czy wszystko działa
if curl -s http://localhost:8000 > /dev/null 2>&1 && curl -s http://localhost:3000 > /dev/null 2>&1; then
    log_success "Aplikacja działa poprawnie!"
else
    log_warning "Aplikacja uruchomiona, ale sprawdź logi w przypadku problemów"
fi
