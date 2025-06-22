#!/usr/bin/env python3
"""
Skrypt do automatycznej aktualizacji importów w projekcie FoodSave AI.
Zamienia wszystkie importy 'src.backend' na 'backend'.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def find_files_with_imports(directory: str, pattern: str = "*.py") -> List[str]:
    """
    Znajduje wszystkie pliki Python zawierające określony wzorzec importu.

    Args:
        directory: Katalog do przeszukania
        pattern: Wzorzec plików do przeszukania

    Returns:
        Lista ścieżek do plików zawierających wzorzec importu
    """
    files_with_imports = []

    for path in Path(directory).rglob(pattern):
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if "from src.backend" in content or "import src.backend" in content:
                    files_with_imports.append(str(path))

    return files_with_imports


def update_imports_in_file(file_path: str) -> Tuple[int, int]:
    """
    Aktualizuje importy w pliku, zamieniając 'src.backend' na 'backend'.

    Args:
        file_path: Ścieżka do pliku

    Returns:
        Krotka (liczba_zmienionych_linii, całkowita_liczba_importów)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Wzorce do zamiany
    pattern1 = r"from src\.backend"
    pattern2 = r"import src\.backend"

    # Zamiana wzorców
    new_content1 = re.sub(pattern1, "from backend", content)
    new_content2 = re.sub(pattern2, "import backend", new_content1)

    # Liczba zmienionych linii
    changed_lines = 0
    if new_content2 != content:
        changed_lines = (
            new_content2.count("from backend")
            + new_content2.count("import backend")
            - content.count("from backend")
            - content.count("import backend")
        )

    # Całkowita liczba importów
    total_imports = content.count("from src.backend") + content.count(
        "import src.backend"
    )

    # Zapisz zmiany
    if new_content2 != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content2)

    return changed_lines, total_imports


def main():
    """Główna funkcja skryptu."""
    print("🔧 Skrypt aktualizacji importów w projekcie FoodSave AI")
    print("=" * 60)

    # Katalog do przeszukania
    directory = "src/backend"
    if len(sys.argv) > 1:
        directory = sys.argv[1]

    print(f"Przeszukiwanie katalogu: {directory}")

    # Znajdź pliki z importami
    files = find_files_with_imports(directory)
    print(f"Znaleziono {len(files)} plików z importami 'src.backend'")

    if not files:
        print("Nie znaleziono plików do aktualizacji.")
        return

    # Aktualizuj importy
    total_changed = 0
    total_imports = 0

    print("\nAktualizacja importów:")
    print("-" * 60)

    for file_path in files:
        changed, imports = update_imports_in_file(file_path)
        total_changed += changed
        total_imports += imports

        status = "✅" if changed > 0 else "⚠️"
        print(f"{status} {file_path}: zmieniono {changed}/{imports} importów")

    print("-" * 60)
    print(
        f"Łącznie zaktualizowano {total_changed}/{total_imports} importów w {len(files)} plikach."
    )

    # Instrukcje po aktualizacji
    print("\n📋 Następne kroki:")
    print("1. Sprawdź zmiany w plikach")
    print("2. Uruchom testy, aby upewnić się, że wszystko działa poprawnie")
    print("3. Zbuduj i uruchom kontenery za pomocą docker-compose")


if __name__ == "__main__":
    main()
