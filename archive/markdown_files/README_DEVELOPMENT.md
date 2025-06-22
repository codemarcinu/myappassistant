# FoodSave AI - Development Environment

## 🚀 Szybki Start

### Wymagania
- Docker i Docker Compose
- Git
- Minimum 8GB RAM (dla Ollama LLM)

### Inicjalizacja środowiska

```bash
# 1. Sklonuj repozytorium
git clone <repository-url>
cd my_ai_assistant

# 2. Uruchom setup development
./scripts/dev-setup.sh setup

# 3. Uruchom aplikację
./scripts/dev-setup.sh start
```

### Dostępne endpointy
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📊 **API Docs**: http://localhost:8000/docs
- 🤖 **Ollama**: http://localhost:11434
- 📈 **Prometheus**: http://localhost:9090
- 📊 **Grafana**: http://localhost:3001 (admin/admin)
- 🗄️ **Redis**: localhost:6379
- 🐘 **PostgreSQL**: localhost:5432

## 🔧 Zarządzanie Środowiskiem

### Podstawowe komendy

```bash
# Uruchomienie aplikacji
./scripts/dev-setup.sh start

# Zatrzymanie aplikacji
./scripts/dev-setup.sh stop

# Restart aplikacji
./scripts/dev-setup.sh restart

# Sprawdzenie statusu
./scripts/dev-setup.sh status

# Wyświetlenie logów
./scripts/dev-setup.sh logs backend
./scripts/dev-setup.sh logs frontend
./scripts/dev-setup.sh logs all

# Monitorowanie logów w czasie rzeczywistym
./scripts/dev-setup.sh monitor backend
./scripts/dev-setup.sh monitor frontend

# Debugowanie (shell access)
./scripts/dev-setup.sh debug backend
./scripts/dev-setup.sh debug frontend

# Czyszczenie środowiska
./scripts/dev-setup.sh cleanup
```

### Alternatywne komendy Docker Compose

```bash
# Uruchomienie z budowaniem
docker-compose -f docker-compose.dev.yml up --build

# Uruchomienie w tle
docker-compose -f docker-compose.dev.yml up -d

# Zatrzymanie
docker-compose -f docker-compose.dev.yml down

# Wyświetlenie logów
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend

# Sprawdzenie statusu
docker-compose -f docker-compose.dev.yml ps
```

## 🔄 Hot Reload

### Backend (FastAPI)
- **Automatyczny reload** przy zmianach w `./src/backend/`
- **Uvicorn** z flagą `--reload`
- **Poetry** do zarządzania zależnościami

### Frontend (Next.js)
- **Automatyczny reload** przy zmianach w `./foodsave-frontend/`
- **Next.js dev server** z hot module replacement
- **TypeScript** compilation w czasie rzeczywistym

## 📁 Struktura Plików

```
my_ai_assistant/
├── Dockerfile.dev.backend          # Backend development image
├── foodsave-frontend/
│   └── Dockerfile.dev.frontend     # Frontend development image
├── docker-compose.dev.yml          # Development services
├── .dockerignore                   # Excluded files from build
├── env.dev.example                 # Environment variables template
├── .env.dev                        # Development environment (create from template)
├── scripts/
│   └── dev-setup.sh               # Development management script
└── README_DEVELOPMENT.md          # This file
```

## 🔧 Konfiguracja

### Zmienne środowiskowe

1. **Skopiuj szablon**:
   ```bash
   cp env.dev.example .env.dev
   ```

2. **Edytuj plik** `.env.dev` i dostosuj wartości:
   ```bash
   # Podstawowe ustawienia
   ENVIRONMENT=development
   DEBUG=true
   LOG_LEVEL=DEBUG

   # Backend
   DATABASE_URL=sqlite+aiosqlite:///./data/foodsave_dev.db
   REDIS_URL=redis://redis:6379

   # AI/ML
   OLLAMA_URL=http://ollama:11434
   OLLAMA_MODEL=gemma:2b

   # Frontend
   NEXT_PUBLIC_API_URL=http://backend:8000
   NEXT_PUBLIC_APP_NAME=FoodSave AI (Dev)
   ```

### Wolumeny Docker

#### Backend
- `./src/backend:/app/src/backend:cached` - Hot reload kodu
- `./data:/app/data` - Dane aplikacji
- `./logs:/app/logs` - Logi
- `./backups:/app/backups` - Backupy

#### Frontend
- `./foodsave-frontend:/app:cached` - Hot reload kodu
- `/app/node_modules` - Zależności Node.js (anonymous volume)
- `/app/.next` - Cache Next.js (anonymous volume)
- `./logs/frontend:/app/logs` - Logi

## 📊 Monitoring i Logi

### Logi
- **Lokalizacja**: `./logs/`
- **Rotacja**: max 10MB, 5 plików
- **Format**: JSON
- **Serwisy**: backend, frontend, ollama, redis, postgres, nginx

### Monitoring
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Metryki**: Automatyczne zbieranie metryk z FastAPI

### Health Checks
Wszystkie serwisy mają skonfigurowane health checks:
- Backend: `GET /health`
- Frontend: `GET /`
- Ollama: `GET /api/version`
- Redis: `PING`
- PostgreSQL: `pg_isready`

## 🐛 Debugowanie

### Backend Debug
```bash
# Shell access do kontenera
./scripts/dev-setup.sh debug backend

# Wyświetlenie logów
./scripts/dev-setup.sh logs backend

# Sprawdzenie procesów
docker-compose -f docker-compose.dev.yml exec backend ps aux
```

### Frontend Debug
```bash
# Shell access do kontenera
./scripts/dev-setup.sh debug frontend

# Wyświetlenie logów
./scripts/dev-setup.sh logs frontend

# Sprawdzenie procesów
docker-compose -f docker-compose.dev.yml exec frontend ps aux
```

### Database Debug
```bash
# Redis CLI
./scripts/dev-setup.sh debug redis

# PostgreSQL
./scripts/dev-setup.sh debug postgres
```

## 🔍 Troubleshooting

### Problem: Backend nie uruchamia się
```bash
# Sprawdź logi
./scripts/dev-setup.sh logs backend

# Sprawdź czy .env.dev istnieje
ls -la .env.dev

# Sprawdź czy port 8000 jest wolny
netstat -tulpn | grep :8000
```

### Problem: Frontend nie uruchamia się
```bash
# Sprawdź logi
./scripts/dev-setup.sh logs frontend

# Sprawdź czy port 3000 jest wolny
netstat -tulpn | grep :3000

# Sprawdź node_modules
docker-compose -f docker-compose.dev.yml exec frontend ls -la node_modules
```

### Problem: Ollama nie odpowiada
```bash
# Sprawdź logi
./scripts/dev-setup.sh logs ollama

# Sprawdź czy model jest pobrany
curl http://localhost:11434/api/tags

# Pobierz model ręcznie
curl -X POST http://localhost:11434/api/pull -d '{"name": "gemma:2b"}'
```

### Problem: Brak pamięci
```bash
# Sprawdź użycie pamięci
docker stats

# Zatrzymaj niepotrzebne kontenery
docker-compose -f docker-compose.dev.yml stop prometheus grafana

# Wyczyść cache Docker
docker system prune -f
```

## 🧹 Czyszczenie

### Częste czyszczenie
```bash
# Zatrzymanie i usunięcie kontenerów
docker-compose -f docker-compose.dev.yml down

# Usunięcie obrazów
docker rmi $(docker images -q foodsave-*) 2>/dev/null || true

# Usunięcie volumes
docker volume prune -f
```

### Pełne czyszczenie
```bash
# Użyj skryptu
./scripts/dev-setup.sh cleanup

# Lub ręcznie
docker-compose -f docker-compose.dev.yml down -v
docker system prune -a -f
rm -rf data/foodsave_dev.db data/vector_store_dev
```

## 📚 Dodatkowe Informacje

### Architektura
- **Backend**: FastAPI + Poetry + SQLite/PostgreSQL
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **AI/ML**: Ollama + LangChain + FAISS
- **Cache**: Redis
- **Monitoring**: Prometheus + Grafana

### Performance
- **Hot reload**: ~1-2 sekundy
- **Build time**: ~5-10 minut (pierwszy raz)
- **Memory usage**: ~4-6GB (z Ollama)
- **Disk usage**: ~2-3GB

### Security
- **Non-root users** w kontenerach
- **Read-only volumes** gdzie możliwe
- **Health checks** dla wszystkich serwisów
- **Environment variables** zamiast hard-coded values

### Development Workflow
1. **Setup**: `./scripts/dev-setup.sh setup`
2. **Start**: `./scripts/dev-setup.sh start`
3. **Develop**: Edytuj kod w `./src/backend/` lub `./foodsave-frontend/`
4. **Monitor**: `./scripts/dev-setup.sh monitor all`
5. **Debug**: `./scripts/dev-setup.sh debug backend`
6. **Stop**: `./scripts/dev-setup.sh stop`

## 🤝 Contributing

### Przed commitem
```bash
# Sprawdź czy wszystko działa
./scripts/dev-setup.sh status

# Uruchom testy (jeśli dostępne)
docker-compose -f docker-compose.dev.yml exec backend pytest
docker-compose -f docker-compose.dev.yml exec frontend npm test

# Sprawdź logi
./scripts/dev-setup.sh logs all
```

### Code Style
- **Backend**: Black + Flake8 + MyPy
- **Frontend**: ESLint + Prettier + TypeScript
- **Docker**: Best practices + multi-stage builds

## 📞 Support

### Logi i diagnostyka
```bash
# Pełne logi wszystkich serwisów
./scripts/dev-setup.sh logs all

# Status wszystkich serwisów
./scripts/dev-setup.sh status

# Informacje o systemie
docker system df
docker info
```

### Dokumentacja
- [Docker Guide](./DOCKER_GUIDE.md)
- [Architecture Documentation](./ARCHITECTURE_DOCUMENTATION.md)
- [API Documentation](http://localhost:8000/docs) (po uruchomieniu)

---

**Uwaga**: To środowisko jest przeznaczone wyłącznie do developmentu. Nie używaj go w produkcji!
