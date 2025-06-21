#!/bin/bash

# FoodSave AI - Development Setup Test Script
# Skrypt do testowania konfiguracji środowiska developerskiego

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

# Test 1: Sprawdzenie wymaganych plików
test_required_files() {
    log_info "Test 1: Sprawdzanie wymaganych plików..."

    local files=(
        "Dockerfile.dev.backend"
        "foodsave-frontend/Dockerfile.dev.frontend"
        "docker-compose.dev.yml"
        ".dockerignore"
        "foodsave-frontend/.dockerignore"
        "env.dev.example"
        "scripts/dev-setup.sh"
        "README_DEVELOPMENT.md"
    )

    local missing_files=()

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_error "✗ $file - BRAK"
            missing_files+=("$file")
        fi
    done

    if [ ${#missing_files[@]} -eq 0 ]; then
        log_success "Wszystkie wymagane pliki istnieją"
        return 0
    else
        log_error "Brakujące pliki: ${missing_files[*]}"
        return 1
    fi
}

# Test 2: Sprawdzenie Dockerfile'ów
test_dockerfiles() {
    log_info "Test 2: Sprawdzanie Dockerfile'ów..."

    local backend_ok=true
    local frontend_ok=true

    # Test backend Dockerfile
    if grep -q "FROM python:3.12-slim" Dockerfile.dev.backend; then
        log_success "✓ Backend Dockerfile używa Python 3.12"
    else
        log_error "✗ Backend Dockerfile nie używa Python 3.12"
        backend_ok=false
    fi

    if grep -q "poetry run uvicorn" Dockerfile.dev.backend; then
        log_success "✓ Backend Dockerfile ma hot-reload"
    else
        log_error "✗ Backend Dockerfile nie ma hot-reload"
        backend_ok=false
    fi

    # Test frontend Dockerfile
    if grep -q "FROM node:20-alpine" foodsave-frontend/Dockerfile.dev.frontend; then
        log_success "✓ Frontend Dockerfile używa Node.js 20"
    else
        log_error "✗ Frontend Dockerfile nie używa Node.js 20"
        frontend_ok=false
    fi

    if grep -q "npm run dev" foodsave-frontend/Dockerfile.dev.frontend; then
        log_success "✓ Frontend Dockerfile ma hot-reload"
    else
        log_error "✗ Frontend Dockerfile nie ma hot-reload"
        frontend_ok=false
    fi

    if [ "$backend_ok" = true ] && [ "$frontend_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test 3: Sprawdzenie docker-compose.dev.yml
test_docker_compose() {
    log_info "Test 3: Sprawdzanie docker-compose.dev.yml..."

    local compose_ok=true

    # Sprawdzenie czy używa nowych Dockerfile'ów
    if grep -q "Dockerfile.dev.backend" docker-compose.dev.yml; then
        log_success "✓ Używa Dockerfile.dev.backend"
    else
        log_error "✗ Nie używa Dockerfile.dev.backend"
        compose_ok=false
    fi

    if grep -q "Dockerfile.dev.frontend" docker-compose.dev.yml; then
        log_success "✓ Używa Dockerfile.dev.frontend"
    else
        log_error "✗ Nie używa Dockerfile.dev.frontend"
        compose_ok=false
    fi

    # Sprawdzenie wolumenów dla hot-reload
    if grep -q "./src/backend:/app/src/backend:cached" docker-compose.dev.yml; then
        log_success "✓ Backend ma wolumen dla hot-reload"
    else
        log_error "✗ Backend nie ma wolumenu dla hot-reload"
        compose_ok=false
    fi

    if grep -q "./foodsave-frontend:/app:cached" docker-compose.dev.yml; then
        log_success "✓ Frontend ma wolumen dla hot-reload"
    else
        log_error "✗ Frontend nie ma wolumenu dla hot-reload"
        compose_ok=false
    fi

    # Sprawdzenie logowania
    if grep -q "max-size: \"10m\"" docker-compose.dev.yml; then
        log_success "✓ Logowanie ma rotację (10MB)"
    else
        log_error "✗ Logowanie nie ma rotacji"
        compose_ok=false
    fi

    if grep -q "max-file: \"5\"" docker-compose.dev.yml; then
        log_success "✓ Logowanie ma limit plików (5)"
    else
        log_error "✗ Logowanie nie ma limitu plików"
        compose_ok=false
    fi

    # Sprawdzenie zmiennych środowiskowych
    if grep -q "env_file:" docker-compose.dev.yml; then
        log_success "✓ Używa pliku .env.dev"
    else
        log_error "✗ Nie używa pliku .env.dev"
        compose_ok=false
    fi

    if [ "$compose_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test 4: Sprawdzenie .dockerignore
test_dockerignore() {
    log_info "Test 4: Sprawdzanie .dockerignore..."

    local ignore_ok=true

    local required_patterns=(
        "node_modules/"
        "__pycache__/"
        ".git/"
        "logs/"
        "*.log"
        ".env"
    )

    for pattern in "${required_patterns[@]}"; do
        if grep -q "$pattern" .dockerignore; then
            log_success "✓ .dockerignore wyklucza: $pattern"
        else
            log_warning "⚠ .dockerignore nie wyklucza: $pattern"
            ignore_ok=false
        fi
    done

    if [ "$ignore_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test 5: Sprawdzenie skryptu dev-setup.sh
test_dev_script() {
    log_info "Test 5: Sprawdzanie skryptu dev-setup.sh..."

    local script_ok=true

    if [ -x "scripts/dev-setup.sh" ]; then
        log_success "✓ Skrypt dev-setup.sh jest wykonywalny"
    else
        log_error "✗ Skrypt dev-setup.sh nie jest wykonywalny"
        script_ok=false
    fi

    # Sprawdzenie czy skrypt ma wymagane funkcje
    local required_functions=(
        "start_dev"
        "stop_dev"
        "show_logs"
        "show_status"
    )

    for func in "${required_functions[@]}"; do
        if grep -q "$func()" scripts/dev-setup.sh; then
            log_success "✓ Skrypt ma funkcję: $func"
        else
            log_warning "⚠ Skrypt nie ma funkcji: $func"
            script_ok=false
        fi
    done

    if [ "$script_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test 6: Sprawdzenie zmiennych środowiskowych
test_env_variables() {
    log_info "Test 6: Sprawdzanie zmiennych środowiskowych..."

    local env_ok=true

    if [ -f "env.dev.example" ]; then
        log_success "✓ Plik env.dev.example istnieje"

        # Sprawdzenie kluczowych zmiennych
        local required_vars=(
            "ENVIRONMENT=development"
            "DATABASE_URL"
            "REDIS_URL"
            "OLLAMA_URL"
            "NEXT_PUBLIC_API_URL"
        )

        for var in "${required_vars[@]}"; do
            if grep -q "$var" env.dev.example; then
                log_success "✓ env.dev.example zawiera: $var"
            else
                log_warning "⚠ env.dev.example nie zawiera: $var"
                env_ok=false
            fi
        done
    else
        log_error "✗ Plik env.dev.example nie istnieje"
        env_ok=false
    fi

    if [ "$env_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test 7: Sprawdzenie dokumentacji
test_documentation() {
    log_info "Test 7: Sprawdzanie dokumentacji..."

    local doc_ok=true

    if [ -f "README_DEVELOPMENT.md" ]; then
        log_success "✓ README_DEVELOPMENT.md istnieje"

        # Sprawdzenie kluczowych sekcji
        local required_sections=(
            "Szybki Start"
            "Hot Reload"
            "Troubleshooting"
            "Debugowanie"
        )

        for section in "${required_sections[@]}"; do
            if grep -q "$section" README_DEVELOPMENT.md; then
                log_success "✓ README zawiera sekcję: $section"
            else
                log_warning "⚠ README nie zawiera sekcji: $section"
                doc_ok=false
            fi
        done
    else
        log_error "✗ README_DEVELOPMENT.md nie istnieje"
        doc_ok=false
    fi

    if [ "$doc_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# Główna funkcja testowa
main() {
    echo "🧪 FoodSave AI - Development Setup Test"
    echo "========================================"
    echo ""

    local tests=(
        "test_required_files"
        "test_dockerfiles"
        "test_docker_compose"
        "test_dockerignore"
        "test_dev_script"
        "test_env_variables"
        "test_documentation"
    )

    local passed=0
    local total=${#tests[@]}

    for test in "${tests[@]}"; do
        echo ""
        if $test; then
            ((passed++))
        fi
    done

    echo ""
    echo "========================================"
    echo "📊 Wyniki testów: $passed/$total testów przeszło"

    if [ $passed -eq $total ]; then
        log_success "🎉 Wszystkie testy przeszły! Środowisko development jest gotowe."
        echo ""
        echo "🚀 Możesz teraz uruchomić:"
        echo "   ./scripts/dev-setup.sh setup"
        echo "   ./scripts/dev-setup.sh start"
    else
        log_error "❌ Niektóre testy nie przeszły. Sprawdź powyższe błędy."
        exit 1
    fi
}

# Uruchomienie testów
main "$@"
