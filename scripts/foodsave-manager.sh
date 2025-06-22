#!/bin/bash

# ================================================
# FoodSave AI - Manager Script
# Kompleksowe narzędzie do zarządzania projektem FoodSave AI
# ================================================

# Kolory do formatowania tekstu
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Ustawienie ścieżki bazowej
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
cd "$BASE_DIR"

# Wymagane modele
REQUIRED_MODELS=(
  "gemma3:12b"
  "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
  "nomic-embed-text"
)

# Grupy kontenerów
CORE_SERVICES="ollama backend frontend postgres"
CACHE_SERVICES="redis"
MONITORING_SERVICES="prometheus grafana"
LOGGING_SERVICES="loki promtail"
ALL_SERVICES="$CORE_SERVICES $CACHE_SERVICES $MONITORING_SERVICES $LOGGING_SERVICES"

# Funkcja do wyświetlania nagłówka
print_header() {
  clear
  echo -e "${BLUE}=================================================="
  echo -e "       FoodSave AI - Manager Script v1.0          "
  echo -e "==================================================${NC}"
  echo ""
}

# Funkcja do sprawdzania czy Docker jest uruchomiony
check_docker() {
  if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker nie jest uruchomiony. Uruchom Docker i spróbuj ponownie.${NC}"
    exit 1
  else
    echo -e "${GREEN}✅ Docker jest uruchomiony${NC}"
  fi
}

# Funkcja do sprawdzania czy kontener Ollama jest uruchomiony
check_ollama_container() {
  if docker ps | grep -q "foodsave-ollama"; then
    echo -e "${GREEN}✅ Kontener Ollama jest uruchomiony${NC}"
    return 0
  else
    echo -e "${YELLOW}⚠️ Kontener Ollama nie jest uruchomiony${NC}"
    return 1
  fi
}

# Funkcja do sprawdzania dostępności modeli
check_models() {
  echo -e "${BLUE}Sprawdzanie dostępności modeli...${NC}"

  if ! check_ollama_container; then
    echo -e "${YELLOW}⚠️ Nie można sprawdzić modeli - kontener Ollama nie jest uruchomiony${NC}"
    return 1
  fi

  # Pobierz listę zainstalowanych modeli
  INSTALLED_MODELS=$(docker exec foodsave-ollama ollama list | awk 'NR>1 {print $1}')

  # Sprawdź każdy wymagany model
  MISSING_MODELS=()
  for model in "${REQUIRED_MODELS[@]}"; do
    if echo "$INSTALLED_MODELS" | grep -q "$model"; then
      echo -e "${GREEN}✅ Model $model jest zainstalowany${NC}"
    else
      echo -e "${YELLOW}⚠️ Model $model nie jest zainstalowany${NC}"
      MISSING_MODELS+=("$model")
    fi
  done

  # Jeśli są brakujące modele, zapytaj czy je pobrać
  if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Wykryto brakujące modele. Czy chcesz je pobrać? [T/n]${NC}"
    read -r answer
    if [[ "$answer" != "n" && "$answer" != "N" ]]; then
      for model in "${MISSING_MODELS[@]}"; do
        echo -e "${BLUE}Pobieranie modelu $model...${NC}"
        docker exec foodsave-ollama ollama pull "$model"
        if [ $? -eq 0 ]; then
          echo -e "${GREEN}✅ Model $model został pomyślnie pobrany${NC}"
        else
          echo -e "${RED}❌ Błąd podczas pobierania modelu $model${NC}"
        fi
      done
    fi
  fi
}

# Funkcja do sprawdzania GPU
check_gpu() {
  echo -e "${BLUE}Sprawdzanie dostępności GPU...${NC}"

  if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ Wykryto GPU NVIDIA${NC}"
    nvidia-smi
    return 0
  else
    echo -e "${YELLOW}⚠️ Nie wykryto GPU NVIDIA, będzie używane CPU${NC}"
    return 1
  fi
}

# Funkcja do wyboru grup kontenerów do uruchomienia
select_services() {
  echo -e "${BLUE}Wybierz, które grupy kontenerów chcesz uruchomić:${NC}"
  echo "1. Podstawowe (ollama, backend, frontend, postgres)"
  echo "2. Podstawowe + Cache (+ redis)"
  echo "3. Podstawowe + Monitoring (+ prometheus, grafana)"
  echo "4. Podstawowe + Logi (+ loki, promtail)"
  echo "5. Wszystkie kontenery"

  read -r choice

  case $choice in
    1)
      echo -e "${BLUE}Wybrano podstawowe kontenery${NC}"
      SERVICES="$CORE_SERVICES"
      ;;
    2)
      echo -e "${BLUE}Wybrano podstawowe kontenery + cache${NC}"
      SERVICES="$CORE_SERVICES $CACHE_SERVICES"
      ;;
    3)
      echo -e "${BLUE}Wybrano podstawowe kontenery + monitoring${NC}"
      SERVICES="$CORE_SERVICES $MONITORING_SERVICES"
      ;;
    4)
      echo -e "${BLUE}Wybrano podstawowe kontenery + logi${NC}"
      SERVICES="$CORE_SERVICES $LOGGING_SERVICES"
      ;;
    5)
      echo -e "${BLUE}Wybrano wszystkie kontenery${NC}"
      SERVICES="$ALL_SERVICES"
      ;;
    *)
      echo -e "${YELLOW}Nieprawidłowy wybór, uruchamiam podstawowe kontenery${NC}"
      SERVICES="$CORE_SERVICES"
      ;;
  esac

  echo -e "${GREEN}Wybrane usługi: $SERVICES${NC}"
  return 0
}

# Funkcja do uruchamiania kontenerów
start_containers() {
  echo -e "${BLUE}Uruchamianie kontenerów...${NC}"

  # Jeśli nie podano usług, zapytaj użytkownika
  if [ -z "$1" ]; then
    select_services
  else
    SERVICES="$1"
  fi

  # Uruchom wybrane kontenery
  for service in $SERVICES; do
    echo -e "${BLUE}Uruchamianie kontenera $service...${NC}"
    docker-compose -f docker-compose.yaml up -d $service

    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Kontener $service uruchomiony pomyślnie${NC}"
    else
      echo -e "${RED}❌ Błąd podczas uruchamiania kontenera $service${NC}"
    fi
  done

  echo -e "${GREEN}✅ Wybrane kontenery zostały uruchomione${NC}"
  echo ""
  echo -e "${BLUE}Informacje o dostępie:${NC}"
  echo -e "* Backend API: ${CYAN}http://localhost:8000${NC}"
  echo -e "* Frontend App: ${CYAN}http://localhost:3000${NC}"

  # Wyświetl dodatkowe informacje w zależności od uruchomionych usług
  if echo "$SERVICES" | grep -q "prometheus"; then
    echo -e "* Prometheus: ${CYAN}http://localhost:9090${NC}"
  fi

  if echo "$SERVICES" | grep -q "grafana"; then
    echo -e "* Grafana: ${CYAN}http://localhost:3001${NC} (admin/admin)"
  fi
}

# Funkcja do zatrzymywania kontenerów
stop_containers() {
  echo -e "${BLUE}Zatrzymywanie kontenerów...${NC}"

  docker-compose -f docker-compose.yaml down

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Kontenery zostały zatrzymane pomyślnie${NC}"
  else
    echo -e "${RED}❌ Błąd podczas zatrzymywania kontenerów${NC}"
  fi
}

# Funkcja do restartowania wybranego kontenera
restart_container() {
  echo -e "${BLUE}Dostępne kontenery:${NC}"

  # Pobierz listę kontenerów
  CONTAINERS=$(docker-compose -f docker-compose.yaml ps --services)

  # Wyświetl listę kontenerów z numerami
  i=1
  declare -A container_map
  for container in $CONTAINERS; do
    echo -e "$i. $container"
    container_map[$i]=$container
    ((i++))
  done

  echo -e "$i. Wszystkie kontenery"

  # Zapytaj użytkownika, który kontener chce zrestartować
  echo ""
  echo -e "${BLUE}Który kontener chcesz zrestartować? (podaj numer)${NC}"
  read -r choice

  # Sprawdź czy wybór jest poprawny
  if [[ "$choice" =~ ^[0-9]+$ ]]; then
    if [ "$choice" -eq "$i" ]; then
      # Restart wszystkich kontenerów
      echo -e "${BLUE}Restartowanie wszystkich kontenerów...${NC}"
      docker-compose -f docker-compose.yaml restart
      if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Wszystkie kontenery zostały zrestartowane pomyślnie${NC}"
      else
        echo -e "${RED}❌ Błąd podczas restartowania kontenerów${NC}"
      fi
    elif [ "$choice" -ge 1 ] && [ "$choice" -lt "$i" ]; then
      # Restart wybranego kontenera
      selected_container=${container_map[$choice]}
      echo -e "${BLUE}Restartowanie kontenera $selected_container...${NC}"
      docker-compose -f docker-compose.yaml restart "$selected_container"
      if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Kontener $selected_container został zrestartowany pomyślnie${NC}"
      else
        echo -e "${RED}❌ Błąd podczas restartowania kontenera $selected_container${NC}"
      fi
    else
      echo -e "${RED}❌ Nieprawidłowy wybór${NC}"
    fi
  else
    echo -e "${RED}❌ Nieprawidłowy wybór${NC}"
  fi
}

# Funkcja do wyświetlania logów
show_logs() {
  echo -e "${BLUE}Dostępne kontenery:${NC}"

  # Pobierz listę kontenerów
  CONTAINERS=$(docker-compose -f docker-compose.yaml ps --services)

  # Wyświetl listę kontenerów z numerami
  i=1
  declare -A container_map
  for container in $CONTAINERS; do
    echo -e "$i. $container"
    container_map[$i]=$container
    ((i++))
  done

  # Zapytaj użytkownika, którego kontenera logi chce zobaczyć
  echo ""
  echo -e "${BLUE}Którego kontenera logi chcesz zobaczyć? (podaj numer)${NC}"
  read -r choice

  # Sprawdź czy wybór jest poprawny
  if [[ "$choice" =~ ^[0-9]+$ ]]; then
    if [ "$choice" -ge 1 ] && [ "$choice" -le "$i" ]; then
      # Pokaż logi wybranego kontenera
      selected_container=${container_map[$choice]}
      echo -e "${BLUE}Wyświetlanie logów kontenera $selected_container...${NC}"
      echo -e "${YELLOW}Naciśnij Ctrl+C, aby wyjść${NC}"
      sleep 2
      docker-compose -f docker-compose.yaml logs -f "$selected_container"
    else
      echo -e "${RED}❌ Nieprawidłowy wybór${NC}"
    fi
  else
    echo -e "${RED}❌ Nieprawidłowy wybór${NC}"
  fi
}

# Funkcja do przebudowywania obrazów
rebuild_images() {
  echo -e "${BLUE}Które obrazy chcesz przebudować?${NC}"
  echo "1. Backend"
  echo "2. Frontend"
  echo "3. Wszystkie"

  read -r choice

  case $choice in
    1)
      echo -e "${BLUE}Przebudowywanie obrazu backend...${NC}"
      docker-compose -f docker-compose.yaml build backend
      ;;
    2)
      echo -e "${BLUE}Przebudowywanie obrazu frontend...${NC}"
      docker-compose -f docker-compose.yaml build frontend
      ;;
    3)
      echo -e "${BLUE}Przebudowywanie wszystkich obrazów...${NC}"
      docker-compose -f docker-compose.yaml build
      ;;
    *)
      echo -e "${RED}❌ Nieprawidłowy wybór${NC}"
      return
      ;;
  esac

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Obrazy zostały przebudowane pomyślnie${NC}"

    echo -e "${BLUE}Czy chcesz uruchomić kontenery? [T/n]${NC}"
    read -r answer
    if [[ "$answer" != "n" && "$answer" != "N" ]]; then
      start_containers
    fi
  else
    echo -e "${RED}❌ Błąd podczas przebudowywania obrazów${NC}"
  fi
}

# Funkcja do sprawdzania statusu kontenerów
check_container_status() {
  echo -e "${BLUE}Sprawdzanie statusu kontenerów...${NC}"

  # Pobierz listę wszystkich kontenerów z docker-compose
  ALL_COMPOSE_SERVICES=$(docker-compose -f docker-compose.yaml config --services)

  # Pobierz listę uruchomionych kontenerów
  RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}")

  echo -e "${CYAN}Status kontenerów:${NC}"
  echo -e "${CYAN}------------------${NC}"

  # Sprawdź status każdego kontenera
  for service in $ALL_COMPOSE_SERVICES; do
    if echo "$RUNNING_CONTAINERS" | grep -q "foodsave-$service"; then
      # Pobierz status zdrowia kontenera
      HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' foodsave-$service 2>/dev/null)

      if [ "$HEALTH_STATUS" = "healthy" ]; then
        echo -e "${GREEN}✅ $service: Uruchomiony (zdrowy)${NC}"
      elif [ "$HEALTH_STATUS" = "starting" ]; then
        echo -e "${YELLOW}⚠️ $service: Uruchomiony (uruchamianie)${NC}"
      elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
        echo -e "${RED}❌ $service: Uruchomiony (niezdrowy)${NC}"
      else
        echo -e "${GREEN}✅ $service: Uruchomiony${NC}"
      fi
    else
      echo -e "${RED}❌ $service: Zatrzymany${NC}"
    fi
  done
}

# Funkcja do pełnego uruchomienia (sprawdzenie modeli + uruchomienie kontenerów)
full_startup() {
  print_header
  check_docker
  check_gpu

  # Sprawdź czy kontenery są już uruchomione
  if docker ps | grep -q "foodsave-ollama"; then
    echo -e "${YELLOW}⚠️ Niektóre kontenery są już uruchomione${NC}"
    check_container_status
    echo -e "${BLUE}Czy chcesz zrestartować kontenery? [t/N]${NC}"
    read -r answer
    if [[ "$answer" == "t" || "$answer" == "T" ]]; then
      stop_containers
      start_containers
    else
      echo -e "${BLUE}Czy chcesz uruchomić dodatkowe kontenery? [t/N]${NC}"
      read -r answer
      if [[ "$answer" == "t" || "$answer" == "T" ]]; then
        start_containers
      fi
    fi
  else
    # Uruchom kontenery
    start_containers

    # Poczekaj chwilę, aby kontener Ollama zdążył się uruchomić
    echo -e "${BLUE}Czekam na uruchomienie kontenera Ollama...${NC}"
    sleep 10
  fi

  # Sprawdź modele
  check_models

  # Sprawdź status kontenerów
  check_container_status

  echo -e "${GREEN}✅ System jest gotowy do użycia${NC}"
}

# Funkcja do naprawy zależności backendu
fix_backend_dependencies() {
  echo -e "${BLUE}Naprawianie zależności backendu...${NC}"

  # Sprawdź czy kontener backendu jest uruchomiony
  if ! docker ps | grep -q foodsave-backend; then
    echo -e "${RED}❌ Kontener foodsave-backend nie jest uruchomiony!${NC}"
    echo -e "${YELLOW}Uruchamianie kontenera backendu...${NC}"
    docker-compose up -d backend

    if [ $? -ne 0 ]; then
      echo -e "${RED}❌ Nie można uruchomić kontenera backendu. Sprawdź logi docker-compose.${NC}"
      return 1
    fi

    echo -e "${GREEN}✅ Kontener backendu uruchomiony${NC}"
    echo -e "${YELLOW}Czekam 5 sekund na inicjalizację kontenera...${NC}"
    sleep 5
  fi

  echo -e "${BLUE}Instalowanie niezbędnych pakietów systemowych...${NC}"
  docker exec foodsave-backend apt-get update
  docker exec foodsave-backend apt-get install -y libopenblas-dev libblas-dev liblapack-dev gfortran

  # Lista wszystkich pakietów Python do instalacji
  echo -e "${BLUE}Instalowanie pakietów Python...${NC}"
  PACKAGES=(
    "structlog==24.1.0"
    "langdetect==1.0.9"
    "redis==5.2.0"
    "pybreaker==1.3.0"
    "slowapi==0.1.9"
    "alembic"
    "asyncpg"
    "dependency_injector>=4.41.0"
    "opentelemetry-api==1.21.0"
    "opentelemetry-sdk==1.21.0"
    "opentelemetry-instrumentation-fastapi==0.42b0"
    "opentelemetry-instrumentation-sqlalchemy==0.42b0"
    "opentelemetry-instrumentation-httpx==0.42b0"
  )

  # Instalacja pakietów Python
  for package in "${PACKAGES[@]}"; do
    echo -e "${YELLOW}Instalowanie $package...${NC}"
    docker exec foodsave-backend pip install --no-cache-dir "$package"
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ $package zainstalowany pomyślnie${NC}"
    else
      echo -e "${RED}❌ Błąd podczas instalacji $package${NC}"
    fi
  done

  # Instalacja faiss-cpu
  echo -e "${BLUE}Instalowanie faiss-cpu...${NC}"
  docker exec foodsave-backend pip install --no-cache-dir faiss-cpu

  if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Próba instalacji faiss-cpu nie powiodła się, próbuję alternatywną wersję...${NC}"
    docker exec foodsave-backend pip install --no-cache-dir faiss-cpu==1.7.0

    if [ $? -ne 0 ]; then
      echo -e "${YELLOW}Próba instalacji alternatywnej wersji nie powiodła się, próbuję z innego źródła...${NC}"
      docker exec foodsave-backend pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple faiss-cpu

      if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Wszystkie próby instalacji faiss-cpu nie powiodły się.${NC}"
        echo -e "${YELLOW}Instalowanie scikit-learn jako alternatywy...${NC}"
        docker exec foodsave-backend pip install --no-cache-dir scikit-learn
        echo -e "${YELLOW}⚠️ Zainstalowano scikit-learn jako alternatywę dla faiss-cpu.${NC}"
      else
        echo -e "${GREEN}✅ faiss-cpu zainstalowany pomyślnie z alternatywnego źródła${NC}"
      fi
    else
      echo -e "${GREEN}✅ faiss-cpu 1.7.0 zainstalowany pomyślnie${NC}"
    fi
  else
    echo -e "${GREEN}✅ faiss-cpu zainstalowany pomyślnie${NC}"
  fi

  # Restart kontenera
  echo -e "${BLUE}Restartowanie kontenera backendu...${NC}"
  docker restart foodsave-backend

  # Sprawdź status
  echo -e "${BLUE}Czekam 5 sekund na uruchomienie kontenera...${NC}"
  sleep 5

  if docker ps | grep -q "foodsave-backend.*healthy"; then
    echo -e "${GREEN}✅ Kontener backendu jest uruchomiony i zdrowy${NC}"
  else
    echo -e "${YELLOW}⚠️ Kontener backendu jest uruchomiony, ale może nie być w pełni zdrowy${NC}"
    echo -e "${YELLOW}Sprawdź logi kontenera:${NC} docker logs foodsave-backend"
  fi

  echo -e "${GREEN}Gotowe! Wszystkie zależności zostały zainstalowane.${NC}"

  echo -e "${BLUE}Naciśnij Enter, aby kontynuować...${NC}"
  read
}

# Główna pętla menu
main_menu() {
  while true; do
    print_header

    echo -e "${BLUE}Wybierz opcję:${NC}"
    echo "1. Sprawdź status systemu"
    echo "2. Uruchom kontenery"
    echo "3. Zatrzymaj kontenery"
    echo "4. Zrestartuj kontener"
    echo "5. Sprawdź dostępność modeli"
    echo "6. Wyświetl logi"
    echo "7. Przebuduj obrazy"
    echo "8. Napraw zależności backendu (w tym faiss-cpu)"
    echo "0. Wyjście"

    echo ""
    read -r -p "Wybór: " choice

    case $choice in
      1)
        check_system_status
        ;;
      2)
        start_containers
        echo -e "${BLUE}Naciśnij Enter, aby kontynuować...${NC}"
        read
        ;;
      3)
        stop_containers
        echo -e "${BLUE}Naciśnij Enter, aby kontynuować...${NC}"
        read
        ;;
      4)
        restart_container
        ;;
      5)
        check_models
        echo -e "${BLUE}Naciśnij Enter, aby kontynuować...${NC}"
        read
        ;;
      6)
        view_logs
        ;;
      7)
        rebuild_images
        ;;
      8)
        fix_backend_dependencies
        ;;
      0)
        echo -e "${GREEN}Do widzenia!${NC}"
        exit 0
        ;;
      *)
        echo -e "${RED}Nieprawidłowy wybór. Spróbuj ponownie.${NC}"
        sleep 2
        ;;
    esac
  done
}

# Uruchom menu główne
main_menu
