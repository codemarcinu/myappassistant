# FoodSave AI - Uruchamianie bez Dockera (Tryb Developerski)

## 🚀 Szybki Start

### 1. Uruchomienie aplikacji
```bash
# Uruchom aplikację z maksymalną ilością informacji diagnostycznych
./scripts/dev-run-simple.sh
```

### 2. Zatrzymanie aplikacji
```bash
# Zatrzymaj aplikację
./scripts/dev-stop.sh
```

## 📋 Wymagania Systemowe

### Obowiązkowe:
- **Python 3.12+** - główny język backend
- **Node.js 18+** - dla frontend (Next.js)
- **npm** - menedżer pakietów Node.js

### Opcjonalne (dla pełnej funkcjonalności):
- **Ollama** - modele AI (gemma3:12b, nomic-embed-text)
- **Redis** - cache i sesje
- **Tesseract OCR** - rozpoznawanie tekstu z obrazów

## 🔧 Co robi skrypt uruchamiający?

### 1. Sprawdza wymagania
- Weryfikuje czy Python, Node.js i npm są zainstalowane
- Sprawdza czy opcjonalne komponenty (Ollama, Redis) są dostępne

### 2. Przygotowuje środowisko
- Tworzy katalogi: `data/`, `logs/`, `backups/`
- Kopiuje `env.dev.example` do `.env` (jeśli nie istnieje)
- Instaluje zależności Python i Node.js

### 3. Uruchamia komponenty
- **Redis** (jeśli dostępny) - cache i sesje
- **Ollama** (jeśli dostępny) - modele AI
- **Backend** (FastAPI) - API na porcie 8000
- **Frontend** (Next.js) - interfejs na porcie 3000

### 4. Wyświetla informacje
- Status wszystkich komponentów
- Linki do endpointów
- PID procesów dla debugowania

## 🌐 Dostępne Endpointy

Po uruchomieniu aplikacji będziesz mieć dostęp do:

### Frontend
- **Aplikacja**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **Chat**: http://localhost:3000/chat

### Backend API
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Status**: http://localhost:8000/api/v1/status

### Komponenty opcjonalne
- **Ollama**: http://localhost:11434 (jeśli zainstalowane)
- **Redis**: localhost:6379 (jeśli zainstalowane)

## 📊 Maksymalna Widoczność Kodu

### Backend (Python/FastAPI)
- **Log Level**: DEBUG - wszystkie szczegóły
- **Hot Reload**: Automatyczne przeładowanie przy zmianach
- **Structured Logging**: JSON format z kontekstem
- **Performance Monitoring**: Czas odpowiedzi, użycie pamięci
- **Error Tracking**: Szczegółowe informacje o błędach

### Frontend (Next.js)
- **Development Mode**: Hot reload, source maps
- **React DevTools**: Dostępne w przeglądarce
- **Console Logging**: Wszystkie logi w konsoli przeglądarki
- **Network Tab**: Wszystkie requesty do API

## 🔍 Debugowanie

### Logi Backend
```bash
# Logi są zapisywane w czasie rzeczywistym
tail -f logs/backend/*.log

# Lub bezpośrednio w terminalu (jeśli uruchomione przez skrypt)
```

### Logi Frontend
```bash
# Logi są wyświetlane w terminalu gdzie uruchomiono skrypt
# Oraz w konsoli przeglądarki (F12 -> Console)
```

### Monitoring w czasie rzeczywistym
```bash
# Sprawdź status aplikacji
curl http://localhost:8000/health

# Szczegółowe metryki
curl http://localhost:8000/metrics

# Status systemu
curl http://localhost:8000/api/v1/status
```

## 🛠️ Konfiguracja

### Plik .env
Skrypt automatycznie tworzy plik `.env` z ustawieniami developerskimi:

```bash
# Edytuj konfigurację
nano .env

# Lub skopiuj z szablonu
cp env.dev.example .env
```

### Główne ustawienia do edycji:
- `LOG_LEVEL=DEBUG` - poziom logowania
- `OLLAMA_MODEL=gemma3:12b` - model AI
- `DATABASE_URL` - baza danych (domyślnie SQLite)
- `REDIS_USE_CACHE=true` - włącz/wyłącz cache

## 🐛 Rozwiązywanie Problemów

### Backend nie uruchamia się
```bash
# Sprawdź logi
tail -f logs/backend/*.log

# Sprawdź zależności
cd src/backend
pip3 list | grep fastapi

# Sprawdź port
lsof -i :8000
```

### Frontend nie uruchamia się
```bash
# Sprawdź zależności
cd foodsave-frontend
npm list

# Sprawdź port
lsof -i :3000

# Wyczyść cache
rm -rf node_modules/.cache
```

### Ollama nie działa
```bash
# Sprawdź czy Ollama jest zainstalowane
ollama --version

# Sprawdź czy model jest dostępny
ollama list

# Pobierz model
ollama pull gemma3:12b
```

### Redis nie działa
```bash
# Sprawdź czy Redis jest zainstalowane
redis-server --version

# Sprawdź czy działa
redis-cli ping
```

## 📈 Monitoring i Metryki

### Wbudowane endpointy monitoringu:
- `/health` - podstawowy health check
- `/metrics` - metryki Prometheus
- `/api/v1/status` - szczegółowy status systemu
- `/api/v1/alerts` - alerty systemowe

### Przykłady użycia:
```bash
# Health check
curl http://localhost:8000/health

# Metryki
curl http://localhost:8000/metrics

# Status systemu
curl http://localhost:8000/api/v1/status | jq

# Alerty
curl http://localhost:8000/api/v1/alerts
```

## 🔄 Hot Reload

### Backend (Python)
- Automatyczne przeładowanie przy zmianach w plikach `.py`
- Uvicorn z flagą `--reload`
- Zmiany są widoczne natychmiast

### Frontend (Next.js)
- Automatyczne przeładowanie przy zmianach w plikach React
- Hot Module Replacement (HMR)
- Zmiany są widoczne w przeglądarce bez odświeżania

## 💡 Wskazówki dla Developera

### 1. Struktura logów
- Wszystkie logi są w formacie JSON
- Zawierają timestamp, poziom, moduł, kontekst
- Łatwe do parsowania i analizy

### 2. Debugowanie AI
- Logi agentów AI są szczegółowe
- Pokazują prompty, odpowiedzi, czas wykonania
- Można śledzić przepływ przez różne agenty

### 3. Performance
- Metryki w czasie rzeczywistym
- Monitoring użycia pamięci i CPU
- Alerty przy przekroczeniu limitów

### 4. Database
- SQLite dla prostoty (development)
- Automatyczne migracje przy starcie
- Seed data dla testowania

## 🚨 Ważne Informacje

### Bezpieczeństwo
- Tryb development - nie dla produkcji
- Debug mode włączony
- Szczegółowe logowanie (może zawierać dane wrażliwe)

### Wydajność
- Hot reload może wpływać na wydajność
- Debug mode zwiększa użycie pamięci
- SQLite może być wolniejszy niż PostgreSQL

### Dane
- Baza danych SQLite w `data/foodsave.db`
- Logi w katalogu `logs/`
- Backupy w katalogu `backups/`

## 📞 Wsparcie

Jeśli napotkasz problemy:

1. **Sprawdź logi** - zawierają szczegółowe informacje
2. **Użyj endpointów monitoringu** - pokazują status systemu
3. **Sprawdź wymagania** - upewnij się że wszystko jest zainstalowane
4. **Restart aplikacji** - `./scripts/dev-stop.sh` + `./scripts/dev-run-simple.sh`

---

**Gotowy do kodowania! 🚀**
