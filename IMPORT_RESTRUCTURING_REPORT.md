# Raport wdrożenia naprawy struktury importów w kontenerze backend

## Streszczenie problemu

Aktualnie występuje niezgodność między strukturą importów w kodzie aplikacji a strukturą plików w kontenerze backend. Powoduje to błędy importu podczas uruchamiania aplikacji w środowisku kontenerowym. Główny problem polega na tym, że kod aplikacji używa importów zaczynających się od `src.backend`, podczas gdy w kontenerze pliki są umieszczone bezpośrednio w katalogu `/app`.

## Analiza obecnej struktury

### Struktura importów w kodzie
Kod aplikacji używa importów względem głównego katalogu projektu, na przykład:
```python
from src.backend.app_factory import create_app
```

### Struktura plików w kontenerze
W kontenerze Docker pliki są kopiowane do katalogu `/app`, a struktura katalogów nie zawiera katalogu `src` jako nadrzędnego dla `backend`.

### Dockerfile.dev
Obecny plik Dockerfile.dev tworzy uproszczony plik `main.py` z nieprawidłową ścieżką importu:
```python
RUN echo 'from app_factory import create_app\napp = create_app()' > main.py
```

### Konfiguracja Poetry
W pliku `pyproject.toml` zdefiniowano pakiety w następujący sposób:
```toml
packages = [
    { include = "backend", from = "src" }
]
```

## Wyniki analizy skryptu fix_test_imports.py

Przeprowadziliśmy analizę struktury importów w projekcie za pomocą rozszerzonego skryptu `fix_test_imports.py`. Wyniki analizy:

```
📊 RAPORT KOMPATYBILNOŚCI IMPORTÓW
============================================================
Przeanalizowano plików: 158
Łączna liczba importów: 973
Importy typu 'src.backend': 23
Importy typu 'backend': 244
Inne importy: 706

Wnioski:
⚠️ Projekt używa mieszanej struktury importów!
   Zalecenie: Ujednolicić importy w całym projekcie.
   Sugerowana strategia: Przekształć wszystkie importy na typ 'backend'.
```

Analiza pokazuje, że:
1. Większość importów w projekcie (244) używa formatu `backend` zamiast `src.backend` (23)
2. Testy używają konsekwentnie importów typu `backend`
3. Istnieje niewielka liczba plików używających formatu `src.backend`

## Zalecane rozwiązania

Mamy dwie główne opcje naprawy:

### Opcja 1: Dostosowanie struktury kontenerów do struktury kodu

1. Zmodyfikować Dockerfile.dev, aby zachować strukturę katalogów `src/backend`
2. Zaktualizować ścieżki w kontenerze, aby uwzględniały katalog `src`
3. Dostosować komendę uruchamiającą aplikację

### Opcja 2: Dostosowanie importów w kodzie do struktury kontenerów

1. Zmodyfikować importy w kodzie, aby używały bezpośrednio modułu `backend` zamiast `src.backend`
2. Zaktualizować skrypty testowe, aby uwzględniały nową strukturę importów
3. Dostosować konfigurację Poetry

## Szczegółowy plan wdrożenia (Opcja 1)

Wybraliśmy Opcję 1 jako mniej inwazyjną, ponieważ wymaga mniej zmian w kodzie aplikacji.

### 1. Modyfikacja Dockerfile.dev

```dockerfile
# Stage 1: Base image with Python and Poetry
FROM python:3.12-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering.
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Stage 2: Install dependencies
FROM base as dependencies

# Copy only files required for dependency installation
COPY pyproject.toml poetry.lock ./

# Install dependencies, without creating a virtualenv in the project
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main --no-interaction --no-ansi

# Stage 3: Application image
FROM dependencies as application

# Copy the entire application source code
COPY . .

# Ensure the main.py file uses the correct import path
RUN echo 'from src.backend.app_factory import create_app\napp = create_app()' > main.py

# Command to run the application
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 2. Aktualizacja docker-compose.dev.yaml

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

### 3. Weryfikacja importów w testach

Sprawdziliśmy pliki testowe i potwierdziliśmy, że używają one poprawnych ścieżek importu zaczynających się od `backend` zamiast `src.backend`. Przykład:

```python
from backend.agents.enhanced_rag_agent import EnhancedRAGAgent
from backend.agents.interfaces import AgentResponse
from backend.core.vector_store import VectorStore
```

### 4. Utworzenie skryptu pomocniczego do weryfikacji importów

Skrypt `fix_test_imports.py` już istnieje i został rozszerzony o funkcje analizy struktury importów w całym projekcie.

## Szczegółowy plan wdrożenia (Opcja 2)

W związku z wynikami analizy skryptu `fix_test_imports.py`, które pokazują, że większość projektu już używa importów typu `backend`, Opcja 2 może być lepszym rozwiązaniem długoterminowym. Należałoby:

### 1. Modyfikacja głównego pliku main.py

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
```

### 2. Aktualizacja importów w kodzie

Należy zaktualizować wszystkie importy w kodzie używające `src.backend` na `backend`. Zidentyfikowane pliki z takimi importami to:

- src/backend/main.py
- Kilka innych plików w strukturze src/backend (łącznie 23 importy)

### 3. Aktualizacja konfiguracji Poetry

```toml
packages = [
    { include = "backend" }
]
```

## Rekomendacja

Na podstawie przeprowadzonej analizy, zmieniamy naszą rekomendację na **Opcję 2**, ponieważ:

1. Większość projektu już używa importów typu `backend`
2. Testy są już skonfigurowane do używania importów typu `backend`
3. Tylko niewielka liczba plików wymaga aktualizacji
4. Ujednolicenie struktury importów ułatwi przyszłą konserwację projektu

## Kroki wdrożenia

1. Zaktualizować główny plik `main.py` zgodnie z podaną specyfikacją
2. Zaktualizować importy w plikach używających `src.backend` na `backend`
3. Zaktualizować konfigurację Poetry w `pyproject.toml`
4. Zaktualizować plik `src/backend/Dockerfile.dev` do używania poprawnej ścieżki importu
5. Zbudować i uruchomić kontenery za pomocą `docker-compose -f docker-compose.dev.yaml up --build`
6. Zweryfikować działanie aplikacji i poprawność importów

## Weryfikacja

Po wdrożeniu zmian należy zweryfikować:

1. Czy aplikacja uruchamia się poprawnie w kontenerze
2. Czy wszystkie testy przechodzą
3. Czy wszystkie funkcjonalności działają zgodnie z oczekiwaniami

## Wnioski

Problem z importami w kontenerze backend wynika z niezgodności między strukturą importów w kodzie a strukturą plików w kontenerze. Na podstawie analizy skryptu `fix_test_imports.py` rekomendujemy ujednolicenie wszystkich importów do formatu `backend` (bez prefiksu `src.`), co jest już dominującym wzorcem w projekcie. To rozwiązanie będzie bardziej spójne z istniejącą strukturą projektu i ułatwi przyszłą konserwację. 