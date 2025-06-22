# Kroki wdrożeniowe naprawy struktury importów

## Wprowadzone zmiany

Na podstawie analizy struktury importów w projekcie FoodSave AI wprowadziliśmy następujące zmiany:

### 1. Aktualizacja głównego pliku main.py

```python
"""
Main application entry point.
"""

import os
import sys

# Fix import paths
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the app from the backend module
from backend.app_factory import create_app

app = create_app()

# This file is just a wrapper to help with imports
```

### 2. Aktualizacja pliku src/backend/main.py

```python
from backend.app_factory import create_app
app = create_app()
```

### 3. Aktualizacja pliku src/backend/Dockerfile.dev

```dockerfile
# Ensure the main.py file uses the correct import path
RUN echo 'from backend.app_factory import create_app\napp = create_app()' > main.py
```

### 4. Aktualizacja konfiguracji Poetry w pyproject.toml

```toml
[tool.poetry]
name = "foodsave-ai"
version = "0.1.0"
description = ""
authors = ["Author Name <author@example.com>"]
packages = [
    { include = "backend" }
]
```

### 5. Aktualizacja docker-compose.dev.yaml

```yaml
# Backend FastAPI - Development Mode
backend:
  build:
    context: .
    dockerfile: src/backend/Dockerfile.dev
  container_name: foodsave-backend-dev
  ports:
    - "8000:8000"
  volumes:
    - ./:/app  # Mapowanie całego katalogu projektu
    - ./logs/backend:/app/logs
  environment:
    - PYTHONPATH=/app
    - ENVIRONMENT=development
    - LOG_LEVEL=DEBUG
  networks:
    - foodsave-network
  depends_on:
    - ollama
  command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level=debug"]
```

## Dalsze kroki

### 1. Aktualizacja pozostałych importów

Należy zaktualizować pozostałe importy typu `src.backend` w projekcie. Zidentyfikowano 23 takie importy, głównie w plikach w katalogu `src/backend`. Można to zrobić ręcznie lub za pomocą skryptu.

### 2. Weryfikacja działania

Po wprowadzeniu zmian należy:

1. Zbudować i uruchomić kontenery:
   ```bash
   docker-compose -f docker-compose.dev.yaml up --build
   ```

2. Sprawdzić logi pod kątem błędów importu:
   ```bash
   docker logs foodsave-backend-dev
   ```

3. Uruchomić testy, aby upewnić się, że wszystko działa poprawnie:
   ```bash
   python run_foodsave_tests.py all
   ```

### 3. Monitorowanie

Po wdrożeniu należy monitorować działanie aplikacji, zwracając szczególną uwagę na:
- Logi błędów importu
- Poprawność działania API
- Wyniki testów

## Podsumowanie

Wprowadzone zmiany ujednolicają strukturę importów w projekcie, dostosowując ją do dominującego wzorca używającego bezpośrednio modułu `backend` bez prefiksu `src.`. To rozwiązanie jest bardziej spójne z istniejącą strukturą projektu i ułatwi przyszłą konserwację. 