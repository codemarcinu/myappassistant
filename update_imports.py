#!/usr/bin/env python3
"""
Skrypt do automatycznej aktualizacji importów w projekcie FoodSave AI.

Ten skrypt przeszukuje pliki Python w projekcie i zamienia importy używające
formatu 'src.backend' na format 'backend', aby zapewnić spójność importów
w całym projekcie i zgodność ze strukturą kontenerów Docker.

Sposób użycia:
    python update_imports.py [--dry-run] [--verbose] [katalog]

Argumenty:
    --dry-run   Tylko wyświetla zmiany, które zostaną wprowadzone, bez faktycznej modyfikacji plików
    --verbose   Wyświetla szczegółowe informacje o przetwarzanych plikach
    katalog     Opcjonalny katalog do przeszukania (domyślnie: bieżący katalog)

Przykłady:
    python update_imports.py --dry-run           # Podgląd zmian bez modyfikacji plików
    python update_imports.py --verbose src/      # Aktualizacja importów w katalogu src z pełnymi informacjami
    python update_imports.py                     # Aktualizacja importów w bieżącym katalogu
"""

import os
import re
import sys
import argparse
from typing import List, Tuple, Dict

# Wzorce importów do zastąpienia
IMPORT_PATTERNS = [
    # from src.backend import X
    (r'from\s+src\.backend\b', 'from backend'),
    # import src.backend.X
    (r'import\s+src\.backend\b', 'import backend'),
]

def find_python_files(directory: str) -> List[str]:
    """
    Znajduje wszystkie pliki Python w podanym katalogu i jego podkatalogach.
    
    Args:
        directory: Katalog do przeszukania
        
    Returns:
        Lista ścieżek do plików Python
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def update_imports_in_file(file_path: str, dry_run: bool = False, verbose: bool = False) -> Tuple[int, Dict[str, int]]:
    """
    Aktualizuje importy w pojedynczym pliku.
    
    Args:
        file_path: Ścieżka do pliku Python
        dry_run: Czy tylko wyświetlić zmiany bez modyfikacji pliku
        verbose: Czy wyświetlać szczegółowe informacje
        
    Returns:
        Krotka (liczba zmienionych linii, słownik ze statystykami zmian)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_count = 0
    pattern_counts = {pattern[0]: 0 for pattern in IMPORT_PATTERNS}
    
    for pattern, replacement in IMPORT_PATTERNS:
        matches = re.findall(pattern, content)
        pattern_counts[pattern] = len(matches)
        content = re.sub(pattern, replacement, content)
    
    total_changes = sum(pattern_counts.values())
    changes_count = total_changes
    
    if original_content != content:
        if verbose:
            print(f"Znaleziono {total_changes} importów do aktualizacji w {file_path}")
            for pattern, count in pattern_counts.items():
                if count > 0:
                    print(f"  - Wzorzec '{pattern}': {count} wystąpień")
        
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if verbose or total_changes > 0:
                print(f"Zaktualizowano {total_changes} importów w {file_path}")
    elif verbose:
        print(f"Brak importów do aktualizacji w {file_path}")
    
    return changes_count, pattern_counts

def main():
    parser = argparse.ArgumentParser(description="Aktualizuje importy z 'src.backend' na 'backend'")
    parser.add_argument('directory', nargs='?', default='.', help="Katalog do przeszukania")
    parser.add_argument('--dry-run', action='store_true', help="Tylko wyświetla zmiany, bez modyfikacji plików")
    parser.add_argument('--verbose', action='store_true', help="Wyświetla szczegółowe informacje")
    args = parser.parse_args()
    
    python_files = find_python_files(args.directory)
    total_files = len(python_files)
    total_changes = 0
    changed_files = 0
    all_pattern_counts = {pattern[0]: 0 for pattern in IMPORT_PATTERNS}
    
    print(f"Znaleziono {total_files} plików Python do przeanalizowania...")
    
    for file_path in python_files:
        changes, pattern_counts = update_imports_in_file(file_path, args.dry_run, args.verbose)
        if changes > 0:
            changed_files += 1
            total_changes += changes
            for pattern, count in pattern_counts.items():
                all_pattern_counts[pattern] += count
    
    print("\n=== PODSUMOWANIE ===")
    print(f"Przeanalizowano plików: {total_files}")
    print(f"Zmieniono plików: {changed_files}")
    print(f"Całkowita liczba zmienionych importów: {total_changes}")
    
    if total_changes > 0:
        print("\nSzczegóły zmian:")
        for pattern, count in all_pattern_counts.items():
            if count > 0:
                print(f"  - Wzorzec '{pattern}': {count} wystąpień")
    
    if args.dry_run:
        print("\nUWAGA: Uruchomiono w trybie --dry-run, żadne pliki nie zostały zmodyfikowane.")
        print("Aby wprowadzić zmiany, uruchom skrypt bez flagi --dry-run.")

if __name__ == "__main__":
    main()
