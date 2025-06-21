#!/bin/bash

# FoodSave AI - Development Setup Script
# Skrypt do łatwego zarządzania środowiskiem developerskim z hot-reload

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

# Sprawdzenie czy Docker jest zainstalowany
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker nie jest zainstalowany. Zainstaluj Docker przed uruchomieniem tego skryptu."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose nie jest zainstalowany. Zainstaluj Docker Compose przed uruchomieniem tego skryptu."
        exit 1
    fi

    log_success "Docker i Docker Compose są dostępne"
}

# Sprawdzenie czy plik .env.dev istnieje
check_env_file() {
    if [ ! -f ".env.dev" ]; then
        log_warning "Plik .env.dev nie istnieje. Tworzę z szablonu..."
        if [ -f "env.dev.example" ]; then
            cp env.dev.example .env.dev
            log_success "Utworzono .env.dev z szablonu env.dev.example"
            log_info "Edytuj .env.dev i dostosuj wartości do swojego środowiska"
        else
            log_error "Nie znaleziono env.dev.example. Utwórz plik .env.dev ręcznie."
            exit 1
        fi
    else
        log_success "Plik .env.dev istnieje"
    fi
}

# Tworzenie katalogów
create_directories() {
    log_step "Tworzenie katalogów dla aplikacji..."

    mkdir -p data
    mkdir -p logs/{backend,frontend,ollama,redis,postgres,nginx}
    mkdir -p backups/{config,database,files,vector_store}
    mkdir -p monitoring/{grafana/{dashboards,datasources},prometheus}

    # Ustawienie uprawnień
    chmod 755 data logs backups monitoring
    chmod 777 logs/*

    log_success "Katalogi utworzone"
}

# Funkcja do uruchamiania aplikacji w trybie development
start_dev() {
    log_step "Uruchamianie aplikacji w trybie development z hot-reload..."

    # Budowanie obrazów z cache
    log_info "Budowanie obrazów..."
    docker-compose -f docker-compose.dev.yml build --no-cache

    # Uruchomienie serwisów
    log_info "Uruchamianie serwisów..."
    docker-compose -f docker-compose.dev.yml up -d

    log_success "Aplikacja uruchomiona w trybie development"

    # Wyświetlenie statusu
    show_status
}

# Funkcja do zatrzymywania aplikacji
stop_dev() {
    log_step "Zatrzymywanie aplikacji..."
    docker-compose -f docker-compose.dev.yml down
    log_success "Aplikacja zatrzymana"
}

# Funkcja do restartowania aplikacji
restart_dev() {
    log_step "Restartowanie aplikacji..."
    stop_dev
    start_dev
}

# Funkcja do wyświetlania logów
show_logs() {
    local service=${1:-backend}
    local lines=${2:-50}

    log_info "Wyświetlanie ostatnich $lines linii logów dla serwisu: $service"

    case $service in
        backend|frontend|ollama|redis|postgres|prometheus|grafana)
            docker-compose -f docker-compose.dev.yml logs --tail=$lines -f "$service"
            ;;
        all)
            docker-compose -f docker-compose.dev.yml logs --tail=$lines -f
            ;;
        *)
            log_error "Nieznany serwis: $service"
            log_info "Dostępne serwisy: backend, frontend, ollama, redis, postgres, prometheus, grafana, all"
            ;;
    esac
}

# Funkcja do sprawdzania statusu
show_status() {
    log_step "Sprawdzanie statusu aplikacji..."

    echo ""
    log_info "Status kontenerów:"
    docker-compose -f docker-compose.dev.yml ps

    echo ""
    log_info "Health checks:"

    # Sprawdzenie health endpoints
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend (FastAPI): OK - http://localhost:8000"
    else
        log_error "Backend (FastAPI): FAILED"
    fi

    if curl -s http://localhost:3000/ > /dev/null 2>&1; then
        log_success "Frontend (Next.js): OK - http://localhost:3000"
    else
        log_error "Frontend (Next.js): FAILED"
    fi

    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        log_success "Ollama (LLM): OK - http://localhost:11434"
    else
        log_error "Ollama (LLM): FAILED"
    fi

    if curl -s http://localhost:6379 > /dev/null 2>&1; then
        log_success "Redis: OK - localhost:6379"
    else
        log_error "Redis: FAILED"
    fi

    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log_success "Prometheus: OK - http://localhost:9090"
    else
        log_error "Prometheus: FAILED"
    fi

    if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
        log_success "Grafana: OK - http://localhost:3001 (admin/admin)"
    else
        log_error "Grafana: FAILED"
    fi

    echo ""
    log_info "Dostępne endpointy:"
    echo "  🌐 Frontend:     http://localhost:3000"
    echo "  🔧 Backend API:  http://localhost:8000"
    echo "  📊 API Docs:     http://localhost:8000/docs"
    echo "  🤖 Ollama:       http://localhost:11434"
    echo "  📈 Prometheus:   http://localhost:9090"
    echo "  📊 Grafana:      http://localhost:3001 (admin/admin)"
    echo "  🗄️  Redis:        localhost:6379"
    echo "  🐘 PostgreSQL:   localhost:5432"
}

# Funkcja do czyszczenia
cleanup_dev() {
    log_warning "Czy na pewno chcesz usunąć wszystkie kontenery, obrazy i volumes? (y/N)"
    read -r response

    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_step "Czyszczenie środowiska development..."

        # Zatrzymanie i usunięcie kontenerów
        docker-compose -f docker-compose.dev.yml down -v

        # Usunięcie obrazów
        docker rmi $(docker images -q foodsave-*) 2>/dev/null || true

        # Usunięcie volumes
        docker volume prune -f

        # Usunięcie danych development
        rm -rf data/foodsave_dev.db
        rm -rf data/vector_store_dev

        log_success "Czyszczenie zakończone"
    else
        log_info "Czyszczenie anulowane"
    fi
}

# Funkcja do monitorowania logów w czasie rzeczywistym
monitor_logs() {
    local service=${1:-all}

    log_info "Uruchamianie monitorowania logów dla: $service"
    log_info "Naciśnij Ctrl+C aby zatrzymać monitorowanie"

    show_logs "$service"
}

# Funkcja do debugowania
debug_service() {
    local service=${1:-backend}

    log_info "Uruchamianie debugowania dla serwisu: $service"

    case $service in
        backend)
            docker-compose -f docker-compose.dev.yml exec backend bash
            ;;
        frontend)
            docker-compose -f docker-compose.dev.yml exec frontend sh
            ;;
        redis)
            docker-compose -f docker-compose.dev.yml exec redis redis-cli
            ;;
        postgres)
            docker-compose -f docker-compose.dev.yml exec postgres psql -U foodsave -d foodsave_dev
            ;;
        *)
            log_error "Nieznany serwis: $service"
            log_info "Dostępne serwisy: backend, frontend, redis, postgres"
            ;;
    esac
}

# Funkcja do wyświetlania pomocy
show_help() {
    echo "FoodSave AI - Development Setup Script"
    echo ""
    echo "Użycie: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Komendy:"
    echo "  setup              - Inicjalizacja środowiska development"
    echo "  start              - Uruchomienie aplikacji w trybie development"
    echo "  stop               - Zatrzymanie aplikacji"
    echo "  restart            - Restart aplikacji"
    echo "  logs [service]     - Wyświetlenie logów serwisu"
    echo "  status             - Sprawdzenie statusu aplikacji"
    echo "  monitor [service]  - Monitorowanie logów w czasie rzeczywistym"
    echo "  debug [service]    - Debugowanie serwisu (shell access)"
    echo "  cleanup            - Usunięcie wszystkich kontenerów i obrazów"
    echo "  help               - Wyświetlenie tej pomocy"
    echo ""
    echo "Serwisy:"
    echo "  backend, frontend, ollama, redis, postgres, prometheus, grafana, all"
    echo ""
    echo "Przykłady:"
    echo "  $0 setup"
    echo "  $0 start"
    echo "  $0 logs backend"
    echo "  $0 monitor frontend"
    echo "  $0 debug backend"
    echo "  $0 status"
    echo ""
    echo "Hot Reload:"
    echo "  Backend:  Automatyczny reload przy zmianach w ./src/backend/"
    echo "  Frontend: Automatyczny reload przy zmianach w ./foodsave-frontend/"
    echo ""
    echo "Logi:"
    echo "  Logi są zapisywane w ./logs/ z rotacją (max 10MB, 5 plików)"
}

# Główna logika
main() {
    local command=${1:-help}
    local option=${2:-}

    case $command in
        setup)
            check_docker
            check_env_file
            create_directories
            log_success "Setup zakończony. Możesz teraz uruchomić aplikację: $0 start"
            ;;
        start)
            check_docker
            check_env_file
            start_dev
            ;;
        stop)
            stop_dev
            ;;
        restart)
            restart_dev
            ;;
        logs)
            show_logs "$option"
            ;;
        status)
            show_status
            ;;
        monitor)
            monitor_logs "$option"
            ;;
        debug)
            debug_service "$option"
            ;;
        cleanup)
            cleanup_dev
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Uruchomienie głównej funkcji
main "$@"
