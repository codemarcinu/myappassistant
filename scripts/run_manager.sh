#!/bin/bash
# Skrypt do uruchamiania FoodSave AI Manager (TUI)
# Gwarantuje uruchomienie w poprawnym środowisku i z poprawnego katalogu.

echo "Uruchamianie FoodSave AI Manager..."

# Przejdź do katalogu, w którym znajduje się skrypt
# To zapewnia, że ścieżki względne będą działać poprawnie
cd "$(dirname "$0")/.."

# Sprawdź, czy istnieje środowisko wirtualne
VENV_PATH="venv/bin/python3"
if [ ! -f "$VENV_PATH" ]; then
    echo "BŁĄD: Nie znaleziono interpretera Python w venv!"
    echo "Upewnij się, że środowisko wirtualne istnieje w $(pwd)/venv"
    read -p "Naciśnij Enter, aby zamknąć."
    exit 1
fi

# Uruchom aplikację TUI używając pełnej ścieżki do interpretera Python
# To jest najbardziej niezawodna metoda, niezależna od aktywacji venv
"$VENV_PATH" -m src.tui_manager.main

echo "Aplikacja zakończyła działanie. Naciśnij Enter, aby zamknąć terminal."
read -p "" 