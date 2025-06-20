# Multi-stage build dla optymalizacji rozmiaru obrazu
FROM python:3.12-slim as base

# Konfiguracja środowiska
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=300 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/venv"

# Dodanie środowiska wirtualnego do PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# Etap budowania zależności
FROM base as builder

# Instalacja systemowych zależności (rzadko się zmieniają)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    swig \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Tworzenie środowiska wirtualnego
RUN python -m venv $VENV_PATH

# Ustawienie katalogu roboczego
WORKDIR $PYSETUP_PATH

# Instalacja podstawowych zależności (rzadko się zmieniają)
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.29.0 \
    python-multipart==0.0.9 \
    slowapi==0.1.9 \
    httpx==0.27.0 \
    pydantic==2.11.0 \
    pydantic-settings==2.0.0 \
    python-dotenv==1.0.0

# Instalacja zależności bazy danych (rzadko się zmieniają)
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    aiosqlite==0.19.0 \
    greenlet==3.0.3 \
    sqlalchemy[asyncio]==2.0.41

# Instalacja dużych pakietów ML osobno dla lepszego cache'owania
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    numpy==2.1.0

# Instalacja torch osobno (największy pakiet)
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    torch==2.7.1+cpu --index-url https://download.pytorch.org/whl/cpu

# Instalacja pozostałych zależności AI/ML
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    ollama==0.1.0 \
    langchain==0.3.25 \
    langchain-community==0.3.25 \
    sentence-transformers==2.2.2 \
    pytesseract==0.3.10 \
    PyMuPDF==1.24.1

# Instalacja faiss-cpu z nowszą wersją
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    faiss-cpu==1.11.0

# Instalacja narzędzi pomocniczych
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    pytz==2024.1 \
    psutil==7.0.0 \
    structlog==24.1.0 \
    pybreaker==1.3.0

# Instalacja dependency-injector z nowszej wersji
RUN pip install --timeout=300 --retries=3 --no-cache-dir \
    dependency-injector>=4.42.0

# Etap produkcyjny
FROM base as production

# Instalacja systemowych zależności runtime
RUN apt-get update && apt-get install -y \
    curl \
    tesseract-ocr \
    libopenblas0-pthread \
    liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Kopiowanie środowiska wirtualnego z etapu builder
COPY --from=builder $VENV_PATH $VENV_PATH

# Tworzenie katalogu aplikacji
RUN mkdir -p /app/data /app/logs
WORKDIR /app

# Kopiowanie kodu aplikacji (to się zmienia najczęściej, więc na końcu)
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
