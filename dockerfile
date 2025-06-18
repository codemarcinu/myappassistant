# Multi-stage build dla optymalizacji rozmiaru obrazu
FROM python:3.12-slim as base

# Konfiguracja środowiska dla Poetry
ENV POETRY_VERSION=1.8.3 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VENV_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Dodanie Poetry do PATH
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Etap budowania zależności
FROM base as builder

# Instalacja systemowych zależności
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalacja Poetry
RUN pip install poetry==$POETRY_VERSION

# Ustawienie katalogu roboczego
WORKDIR $PYSETUP_PATH

# Kopiowanie plików konfiguracji Poetry
COPY pyproject.toml poetry.lock ./

# Konfiguracja Poetry dla kontenera
RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true

# Instalacja zależności produkcyjnych
RUN poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Etap produkcyjny
FROM base as production

# Instalacja systemowych zależności runtime
RUN apt-get update && apt-get install -y \
    curl \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Kopiowanie środowiska wirtualnego z etapu builder
COPY --from=builder $VENV_PATH $VENV_PATH

# Tworzenie katalogu aplikacji
RUN mkdir -p /app/data /app/logs
WORKDIR /app

# Kopiowanie kodu aplikacji
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Tworzenie użytkownika bez uprawnień root
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Domyślna komenda uruchomienia
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
