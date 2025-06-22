# FoodSave AI - Docker Development Environment

Ten dokument zawiera instrukcje dotyczące uruchamiania środowiska deweloperskiego FoodSave AI przy użyciu Docker Compose.

## Wymagania

- Docker Engine 19.03.0+
- Docker Compose V2
- Co najmniej 8GB RAM
- Co najmniej 20GB wolnego miejsca na dysku
- (Opcjonalnie) Karta graficzna NVIDIA z zainstalowanym NVIDIA Container Toolkit dla akceleracji GPU

## Struktura środowiska

Środowisko deweloperskie składa się z następujących usług:

1. **Backend** - aplikacja FastAPI napisana w Pythonie
2. **Frontend** - aplikacja Next.js napisana w TypeScript
3. **Ollama** - lokalne modele językowe
4. **PostgreSQL** - baza danych

## Skrypty pomocnicze

W projekcie dostępne są trzy skrypty pomocnicze do zarządzania środowiskiem:

### Uruchamianie środowiska

```bash
./run_dev_docker.sh
```

Ten skrypt:
- Sprawdza czy Docker jest uruchomiony
- Tworzy niezbędne katalogi dla logów
- Sprawdza istnienie pliku `.env`
- Usuwa istniejące kontenery o tych samych nazwach
- Zatrzymuje istniejące usługi Docker Compose
- Pobiera najnowsze obrazy
- Buduje i uruchamia kontenery

### Sprawdzanie statusu

```bash
./status_dev_docker.sh
```

Ten skrypt:
- Wyświetla listę uruchomionych kontenerów
- Sprawdza stan zdrowia każdej usługi
- Pokazuje adresy URL i porty dla dostępu do usług

### Zatrzymywanie środowiska

```bash
./stop_dev_docker.sh
```

Ten skrypt:
- Zatrzymuje usługi Docker Compose
- Usuwa osierocone kontenery
- Sprawdza i usuwa pozostałe kontenery

## Dostęp do usług

Po uruchomieniu środowiska, usługi są dostępne pod następującymi adresami:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434
- **PostgreSQL**: localhost:5433 (użytkownik: foodsave, hasło: foodsave_dev_password)

## Przeglądanie logów

Aby wyświetlić logi wszystkich usług:

```bash
docker compose -f docker-compose.dev.yaml logs -f
```

Aby wyświetlić logi konkretnej usługi:

```bash
docker compose -f docker-compose.dev.yaml logs -f backend
docker compose -f docker-compose.dev.yaml logs -f frontend
docker compose -f docker-compose.dev.yaml logs -f ollama
docker compose -f docker-compose.dev.yaml logs -f postgres
```

## Rozwiązywanie problemów

### Problem z konfliktami nazw kontenerów

Jeśli pojawi się błąd o konflikcie nazw kontenerów, użyj skryptu `run_dev_docker.sh`, który automatycznie usuwa istniejące kontenery przed uruchomieniem nowych.

### Problem z dostępem do bazy danych

Jeśli backend nie może połączyć się z bazą danych, sprawdź czy:
1. PostgreSQL jest uruchomiony (`./status_dev_docker.sh`)
2. Zmienna środowiskowa DATABASE_URL jest poprawnie skonfigurowana w pliku `.env`

### Problem z dostępem do Ollama

Jeśli backend nie może połączyć się z Ollama, sprawdź czy:
1. Ollama jest uruchomiony (`./status_dev_docker.sh`)
2. Zmienne środowiskowe OLLAMA_URL i OLLAMA_BASE_URL są poprawnie skonfigurowane

### Problem z wolumenami

Jeśli występują problemy z wolumenami, można je usunąć i utworzyć od nowa:

```bash
docker compose -f docker-compose.dev.yaml down -v
./run_dev_docker.sh
```

## Konfiguracja zmiennych środowiskowych

Zmienne środowiskowe są konfigurowane w pliku `.env`. Jeśli plik nie istnieje, zostanie utworzony automatycznie na podstawie `env.dev.example` podczas uruchamiania skryptu `run_dev_docker.sh`.

Najważniejsze zmienne środowiskowe:

- `DATABASE_URL` - URL do bazy danych
- `OLLAMA_URL` - URL do serwisu Ollama
- `OLLAMA_MODEL` - nazwa modelu Ollama do użycia
- `NEXT_PUBLIC_API_URL` - URL do backendu, używany przez frontend

## Wskazówki

1. **Pierwsze uruchomienie** może zająć więcej czasu ze względu na pobieranie obrazów i budowanie kontenerów.
2. **Modele Ollama** są pobierane przy pierwszym użyciu, co może zająć dużo czasu w zależności od rozmiaru modelu.
3. **Akceleracja GPU** jest włączona dla Ollama, jeśli dostępna jest karta NVIDIA z zainstalowanym NVIDIA Container Toolkit.
4. **Dane PostgreSQL** są przechowywane w wolumenie Docker, więc dane nie są tracone po zatrzymaniu kontenerów.

## Zaawansowana konfiguracja

Zaawansowane opcje konfiguracji można znaleźć w pliku `docker-compose.dev.yaml`.

