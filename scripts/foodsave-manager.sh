#!/bin/bash

# FoodSave AI Manager - Niezawodny skrypt zarządzania
# Wersja: 3.1 - Dodane zarządzanie profilami (monitoring)

set -e  # Zatrzymaj na pierwszym błędzie

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Funkcje Pomocnicze ---
print_header() {
    echo -e "${BLUE}===================================${NC}"
    echo -e "${BLUE}    FoodSave AI Manager v3.1     ${NC}"
    echo -e "${BLUE}===================================${NC}"
    echo
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# --- Weryfikacja Wymagań Wstępnych ---
check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker nie jest zainstalowany. Zainstaluj go, aby kontynuować."
        exit 1
    fi
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker nie jest uruchomiony! Uruchom Docker i spróbuj ponownie."
        exit 1
    fi
    if [ ! -f "docker-compose.yaml" ]; then
        print_error "Nie znaleziono pliku 'docker-compose.yaml'. Uruchom skrypt z głównego katalogu projektu."
        exit 1
    fi
}

# --- Główne Funkcje ---

# 1. Pokaż status
show_status() {
    print_header
    print_info "Sprawdzanie statusu kontenerów..."
    echo
    if docker-compose ps | grep -q "Up"; then
        print_success "Niektóre kontenery są uruchomione:"
        docker-compose ps
    else
        print_warning "Wszystkie kontenery są zatrzymane."
    fi
    echo
}

# 2. Uruchom środowisko produkcyjne (symulowane)
start_environment() {
    print_header
    check_prerequisites
    print_info "Uruchamianie środowiska FoodSave AI (tryb standardowy)..."
    docker-compose up -d --build
    print_success "Środowisko zostało uruchomione!"
    echo
    check_and_pull_models # Sprawdź modele po uruchomieniu
    print_info "Frontend: http://localhost:3000"
    echo
}

# 3. Uruchom środowisko z monitoringiem
start_full_environment() {
    print_header
    check_prerequisites
    print_info "Uruchamianie pełnego środowiska FoodSave AI (z monitoringiem)..."
    docker-compose --profile monitoring --profile logging up -d --build
    print_success "Pełne środowisko zostało uruchomione!"
    echo
    check_and_pull_models # Sprawdź modele po uruchomieniu
    print_info "Frontend: http://localhost:3000"
    print_info "Grafana: http://localhost:3001"
    echo
}

# 4. Uruchom środowisko deweloperskie (z hot-reload)
start_dev_environment() {
    print_header
    check_prerequisites
    print_info "Uruchamianie środowiska FoodSave AI (tryb deweloperski z hot-reload)..."
    export BACKEND_DOCKERFILE="src/backend/Dockerfile.dev"
    export FRONTEND_DOCKERFILE="Dockerfile.dev"
    docker-compose up -d --build
    unset BACKEND_DOCKERFILE
    unset FRONTEND_DOCKERFILE
    print_success "Środowisko deweloperskie zostało uruchomione!"
    echo
    check_and_pull_models # Sprawdź modele po uruchomieniu
    print_info "Frontend: http://localhost:3000"
    echo
}

# 5. Uruchom środowisko deweloperskie z monitoringiem
start_dev_full_environment() {
    print_header
    check_prerequisites
    print_info "Uruchamianie pełnego środowiska deweloperskiego (z hot-reload i monitoringiem)..."
    export BACKEND_DOCKERFILE="src/backend/Dockerfile.dev"
    export FRONTEND_DOCKERFILE="Dockerfile.dev"
    docker-compose --profile monitoring --profile logging up -d --build
    unset BACKEND_DOCKERFILE
    unset FRONTEND_DOCKERFILE
    print_success "Pełne środowisko deweloperskie zostało uruchomione!"
    echo
    check_and_pull_models # Sprawdź modele po uruchomieniu
    print_info "Frontend: http://localhost:3000"
    print_info "Grafana: http://localhost:3001"
    echo
}

# 6. Zatrzymaj środowisko
stop_environment() {
    print_header
    print_info "Zatrzymywanie środowiska FoodSave AI..."
    docker-compose down
    print_success "Środowisko zostało zatrzymane!"
    echo
}

# 7. Restartuj środowisko
restart_environment() {
    print_header
    print_info "Restartowanie środowiska (tryb standardowy)..."
    stop_environment
    start_environment
    print_success "Środowisko zostało zrestartowane!"
    echo
}

# 8. Restartuj środowisko z monitoringiem
restart_full_environment() {
    print_header
    print_info "Restartowanie pełnego środowiska (z monitoringiem)..."
    stop_environment
    start_full_environment
    print_success "Pełne środowisko zostało zrestartowane!"
    echo
}

# 9. Sprawdź i pobierz modele AI
check_and_pull_models() {
    print_header
    print_info "Sprawdzanie i pobieranie modeli AI dla Ollama..."
    
    if ! docker-compose ps ollama | grep -q "Up"; then
        print_warning "Kontener Ollama nie jest uruchomiony. Uruchamiam..."
        docker-compose up -d ollama
        print_info "Oczekiwanie na start Ollama..."
        sleep 15
    fi

    REQUIRED_MODELS=(
        "nomic-embed-text:latest"
        "gemma3:12b"
        "speakleash/bielik-4.5b-v3.0-instruct:Q8_0"
    )

    print_info "Pobieranie listy zainstalowanych modeli..."
    INSTALLED_MODELS=$(docker-compose exec -T ollama ollama list)
    
    for model in "${REQUIRED_MODELS[@]}"; do
        # Uproszczone sprawdzanie, szuka nazwy modelu bez taga
        model_name=$(echo "$model" | cut -d':' -f1)
        if echo "$INSTALLED_MODELS" | grep -q "$model_name"; then
            print_success "Model '$model_name' jest już zainstalowany."
        else
            print_warning "Model '$model' nie znaleziony. Rozpoczynam pobieranie..."
            if docker-compose exec -T ollama ollama pull "$model"; then
                print_success "Model '$model' został pomyślnie pobrany."
            else
                print_error "Nie udało się pobrać modelu '$model'. Sprawdź logi kontenera ollama."
            fi
        fi
    done
    print_success "Weryfikacja modeli zakończona."
    echo
}

# 10. Napraw zależności backendu
fix_backend_deps() {
    print_header
    print_info "Instalowanie/aktualizowanie zależności backendu z requirements.txt..."
    check_prerequisites
    
    if ! docker-compose ps backend | grep -q "Up"; then
        print_warning "Backend nie jest uruchomiony. Uruchamiam..."
        docker-compose up -d backend
        sleep 5
    fi
    
    print_info "Instalowanie zależności..."
    docker-compose exec -T backend pip install --no-cache-dir -r src/backend/requirements.txt
    
    print_success "Zależności backendu zostały zaktualizowane!"
    print_info "Zrestartuj backend, aby zmiany weszły w życie (użyj opcji 'restart')."
    echo
}

# 11. Uruchom testy
run_tests() {
    print_header
    print_info "Uruchamianie testów backendu..."
    check_prerequisites
    if ! docker-compose ps backend | grep -q "Up"; then
        print_warning "Backend nie jest uruchomiony. Uruchamiam na potrzeby testów..."
        docker-compose up -d backend
        sleep 5
    fi
    docker-compose exec backend pytest src/tests
    print_success "Testowanie zakończone."
    echo
}

# 12. Pokaż logi
show_logs() {
    print_header
    print_info "Wybierz kontener do wyświetlenia logów. Naciśnij Ctrl+C, aby powrócić do menu."
    containers=($(docker-compose ps --services))

    if [ ${#containers[@]} -eq 0 ]; then
        print_warning "Brak uruchomionych kontenerów."
        return
    fi

    select container in "${containers[@]}" "Wszystkie"; do
        if [ "$container" == "Wszystkie" ]; then
            print_info "Wyświetlanie logów wszystkich kontenerów... (Ctrl+C aby wyjść)"
            docker-compose logs -f || true
            break
        elif [ -n "$container" ]; then
            print_info "Wyświetlanie logów kontenera: $container (Ctrl+C aby wyjść)"
            docker-compose logs -f "$container" || true
            break
        else
            print_error "Nieprawidłowy wybór."
        fi
    done
    echo
}

# 13. Wyczyść środowisko
clean_environment() {
    print_header
    read -p "Czy na pewno chcesz usunąć WSZYSTKIE kontenery, sieci i wolumeny (dane DB!)? [t/N] " choice
    if [[ "$choice" =~ ^[Tt]$ ]]; then
        print_info "Zatrzymywanie i usuwanie kontenerów, sieci i wolumenów..."
        docker-compose down -v --remove-orphans
        print_info "Usuwanie nieużywanych obrazów i cache budowania..."
        docker system prune -af
        print_success "Środowisko zostało gruntownie wyczyszczone."
    else
        print_info "Anulowano czyszczenie."
    fi
    echo
}

# 14. Otwórz powłokę w kontenerze
exec_shell() {
    print_header
    print_info "Wybierz kontener, w którym chcesz otworzyć powłokę bash:"
    running_containers=($(docker-compose ps --services --filter "status=running"))
    
    if [ ${#running_containers[@]} -eq 0 ]; then
        print_warning "Brak uruchomionych kontenerów."
        return
    fi
    
    select container in "${running_containers[@]}"; do
        if [ -n "$container" ]; then
            print_info "Otwieranie powłoki w kontenerze: $container..."
            docker-compose exec "$container" /bin/bash
            break
        else
            print_error "Nieprawidłowy wybór."
        fi
    done
    echo
}

# --- Menu Główne ---
show_menu() {
    while true; do
        print_header
        echo "Wybierz opcję:"
        echo " 1. Pokaż status"
        echo
        echo " 2. Uruchom środowisko (standard)"
        echo " 3. Uruchom środowisko z monitoringiem"
        echo " 4. Uruchom środowisko (deweloperskie, hot-reload)"
        echo " 5. Uruchom środowisko deweloperskie z monitoringiem"
        echo
        echo " 6. Zatrzymaj środowisko"
        echo " 7. Restartuj środowisko (standard)"
        echo " 8. Restartuj środowisko z monitoringiem"
        echo
        echo " 9. Sprawdź/Pobierz modele AI"
        echo " 10. Napraw zależności backendu"
        echo " 11. Uruchom testy backendu"
        echo
        echo " 12. Pokaż logi"
        echo " 13. Wyczyść środowisko (uwaga: usuwa dane!)"
        echo " 14. Otwórz powłokę w kontenerze"
        echo " 0. Wyjście"
        echo
        
        read -p "Twój wybór (0-14): " choice
        echo
        
        case $choice in
            1) show_status ;;
            2) start_environment ;;
            3) start_full_environment ;;
            4) start_dev_environment ;;
            5) start_dev_full_environment ;;
            6) stop_environment ;;
            7) restart_environment ;;
            8) restart_full_environment ;;
            9) check_and_pull_models ;;
            10) fix_backend_deps ;;
            11) run_tests ;;
            12) show_logs ;;
            13) clean_environment ;;
            14) exec_shell ;;
            0) print_info "Do widzenia!"; exit 0 ;;
            *) print_error "Nieprawidłowy wybór. Spróbuj ponownie." ;;
        esac
        
        echo; read -p "Naciśnij Enter, aby kontynuować..."; clear
    done
}

# --- Obsługa Argumentów Wiersza Poleceń ---
if [ $# -eq 0 ]; then
    show_menu
else
    case "$1" in
        status) show_status ;;
        start) start_environment ;;
        start-full) start_full_environment ;;
        dev) start_dev_environment ;;
        dev-full) start_dev_full_environment ;;
        stop) stop_environment ;;
        restart) restart_environment ;;
        restart-full) restart_full_environment ;;
        models) check_and_pull_models ;;
        fix) fix_backend_deps ;;
        test) run_tests ;;
        logs) show_logs "${2:-}" ;;
        clean) clean_environment ;;
        exec) exec_shell ;;
        menu) show_menu ;;
        *)
            print_error "Nieznana opcja: $1"
            echo "Użycie: $0 [status|start|start-full|dev|dev-full|stop|restart|restart-full|models|fix|test|logs|clean|exec|menu]"
            exit 1
            ;;
    esac
fi