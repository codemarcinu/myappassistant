#!/usr/bin/env python3
"""
FoodSave AI Test Runner

Ten skrypt uruchamia testy dla systemu FoodSave AI.
Możesz wybrać kategorię testów do uruchomienia lub uruchomić wszystkie testy.
"""

import argparse
import os
import subprocess
import sys
from typing import List

# Definicje kategorii testów
TEST_CATEGORIES = {
    "receipt": ["tests/test_receipt_processing_fixed.py"],
    "weather": ["tests/test_weather_agent_fixed.py"],
    "rag": ["tests/test_rag_system_fixed.py"],
    "shopping": ["tests/test_shopping_conversation_fixed.py"],
    "search": ["tests/test_search_agent_fixed.py"],
    "ocr": [
        "tests/unit/test_ocr_processing.py",
        "tests/unit/test_ocr_agent.py",
        "tests/unit/test_receipt_endpoints.py",
    ],
    "ocr_simplified": [
        "tests/unit/test_ocr_simplified.py",
        "tests/unit/test_receipt_endpoints_simplified.py",
    ],
    "all": [
        "tests/test_receipt_processing_fixed.py",
        "tests/test_weather_agent_fixed.py",
        "tests/test_rag_system_fixed.py",
        "tests/test_search_agent_fixed.py",
        "tests/test_shopping_conversation_fixed.py",
        "tests/unit/test_ocr_simplified.py",
        "tests/unit/test_receipt_endpoints_simplified.py",
    ],
}


def list_categories() -> None:
    """Wyświetla dostępne kategorie testów"""
    print("Dostępne kategorie testów:")
    for category in TEST_CATEGORIES:
        if category == "all":
            print(f"  {category} - wszystkie testy")
        else:
            print(f"  {category} - {', '.join(TEST_CATEGORIES[category])}")


def run_tests(categories: List[str], verbose: bool = False) -> int:
    """
    Uruchamia testy dla wybranych kategorii

    Args:
        categories: Lista kategorii testów do uruchomienia
        verbose: Czy wyświetlać szczegółowe informacje

    Returns:
        Kod wyjścia (0 - sukces, inny - błąd)
    """
    test_files = []

    # Zbierz wszystkie pliki testów do uruchomienia
    for category in categories:
        if category in TEST_CATEGORIES:
            test_files.extend(TEST_CATEGORIES[category])
        else:
            print(f"Nieznana kategoria: {category}")
            return 1

    # Usuń duplikaty
    test_files = list(set(test_files))

    # Sprawdź, czy wszystkie pliki istnieją
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"Plik testu nie istnieje: {test_file}")
            return 1

    # Przygotuj argumenty dla pytest
    pytest_args = ["python", "-m", "pytest"]
    if verbose:
        pytest_args.append("-v")
    pytest_args.extend(test_files)

    print(f"Uruchamiam testy: {' '.join(test_files)}")

    # Uruchom testy
    try:
        result = subprocess.run(pytest_args)
        return result.returncode
    except Exception as e:
        print(f"Błąd podczas uruchamiania testów: {e}")
        return 1


def main() -> int:
    """Główna funkcja skryptu"""
    parser = argparse.ArgumentParser(description="FoodSave AI Test Runner")
    parser.add_argument(
        "categories",
        nargs="*",
        default=["all"],
        help="Kategorie testów do uruchomienia (domyślnie: all)",
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="Wyświetl dostępne kategorie testów"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Wyświetl szczegółowe informacje"
    )

    args = parser.parse_args()

    # Aktywuj wirtualne środowisko, jeśli istnieje
    venv_path = os.path.join(os.getcwd(), "venv", "bin", "activate")
    if os.path.exists(venv_path):
        os.environ["PATH"] = (
            os.path.join(os.getcwd(), "venv", "bin") + os.pathsep + os.environ["PATH"]
        )

    # Wyświetl dostępne kategorie
    if args.list:
        list_categories()
        return 0

    # Uruchom testy
    return run_tests(args.categories, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
