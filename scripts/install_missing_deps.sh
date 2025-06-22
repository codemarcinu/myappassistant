#!/bin/bash

echo "UWAGA: Ten skrypt jest przestarzały. Zalecamy używanie ./scripts/foodsave-manager.sh (opcja 8) do naprawy zależności backendu."
echo "Czy chcesz kontynuować używanie tego skryptu? [t/N]"
read -r answer

if [[ "$answer" != "t" && "$answer" != "T" ]]; then
  echo "Anulowano. Uruchom ./scripts/foodsave-manager.sh, aby naprawić zależności."
  exit 0
fi

# Skrypt do instalacji brakujących zależności w kontenerze backendu
echo "Instalowanie brakujących zależności w kontenerze backendu..."

# Lista pakietów do instalacji (bez faiss-cpu)
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
)

# Instalacja pakietów standardowych
for package in "${PACKAGES[@]}"; do
  echo "Instalowanie $package..."
  docker exec foodsave-backend pip install --no-cache-dir "$package"
  if [ $? -eq 0 ]; then
    echo "✅ $package zainstalowany pomyślnie"
  else
    echo "❌ Błąd podczas instalacji $package"
  fi
done

# Specjalna obsługa dla faiss-cpu
echo "Instalowanie faiss-cpu (próba 1 - przez pip)..."
docker exec foodsave-backend pip install --no-cache-dir faiss-cpu
if [ $? -ne 0 ]; then
  echo "Próba 1 nieudana, próbuję alternatywną wersję..."

  # Próba 2: Instalacja przez conda
  echo "Instalowanie faiss-cpu (próba 2 - przez conda)..."
  docker exec foodsave-backend pip install --no-cache-dir conda
  docker exec foodsave-backend conda install -c conda-forge faiss-cpu -y

  if [ $? -ne 0 ]; then
    echo "Próba 2 nieudana, próbuję instalację z GitHub..."

    # Próba 3: Instalacja alternatywnej biblioteki
    echo "Instalowanie faiss-cpu (próba 3 - alternatywa)..."
    docker exec foodsave-backend pip install --no-cache-dir faiss-cpu==1.7.0

    if [ $? -ne 0 ]; then
      echo "Próba 3 nieudana, instaluję alternatywną bibliotekę - scikit-learn dla podobnych funkcji..."
      docker exec foodsave-backend pip install --no-cache-dir scikit-learn
      echo "⚠️ Faiss nie został zainstalowany, zainstalowano scikit-learn jako alternatywę"
    else
      echo "✅ faiss-cpu zainstalowany pomyślnie (wersja 1.7.0)"
    fi
  else
    echo "✅ faiss-cpu zainstalowany pomyślnie przez conda"
  fi
else
  echo "✅ faiss-cpu zainstalowany pomyślnie"
fi

echo "Restartowanie kontenera backendu..."
docker restart foodsave-backend

echo "Gotowe! Sprawdź logi backendu, aby upewnić się, że wszystko działa poprawnie."
