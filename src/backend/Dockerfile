FROM python:3.12-slim

WORKDIR /app

# Zainstaluj poetry
RUN pip install poetry

# Skonfiguruj poetry, aby nie tworzyło wirtualnego środowiska wewnątrz kontenera
RUN poetry config virtualenvs.create false

# Skopiuj pliki zależności
COPY pyproject.toml poetry.lock ./

# Zainstaluj zależności (bez instalowania samego projektu, tylko jego zależności)
RUN poetry install --no-interaction --no-ansi --without dev --no-root

# Skopiuj kod aplikacji
COPY src/backend/ ./backend

# Ustaw PYTHONPATH, aby Python mógł znaleźć moduły
ENV PYTHONPATH=/app

# Uruchom aplikację
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
