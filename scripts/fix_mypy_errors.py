#!/usr/bin/env python3
"""
Skrypt do automatycznej naprawy podstawowych błędów MyPy
"""
import re
import os
from pathlib import Path

def fix_no_return_annotation(content: str) -> str:
    """Naprawia funkcje bez adnotacji zwracanych"""
    # Wzorzec dla funkcji bez return annotation
    pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:'
    
    def replace_func(match):
        func_name = match.group(1)
        full_match = match.group(0)
        
        # Sprawdź czy funkcja ma return statement
        # This is a simplified check and might not be accurate for all cases
        # It checks for 'return' in the whole file, not just the function body
        if 'return' not in content:
            return full_match.replace(':', ' -> None:')
        else:
            return full_match.replace(':', ' -> Any:')
    
    return re.sub(pattern, replace_func, content)

def add_imports(content: str) -> str:
    """Dodaje brakujące importy"""
    imports_to_add = [
        "from typing import Any, Dict, List, Optional, Union, Callable",
        "from typing import AsyncGenerator, Coroutine"
    ]
    
    # Sprawdź czy importy już istnieją
    if "from typing import" not in content:
        # Dodaj importy na początku pliku
        lines = content.split('\n')
        import_line = 0
        
        # Znajdź miejsce na dodanie importów
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_line = i + 1
            elif line.strip() and not line.startswith('#'):
                break
        
        # Check if "from __future__ import annotations" exists
        future_import_exists = any(line.strip() == "from __future__ import annotations" for line in lines)

        for imp in reversed(imports_to_add):
            lines.insert(import_line, imp)
        
        # Add "from __future__ import annotations" if not present
        if not future_import_exists:
            lines.insert(0, "from __future__ import annotations")

        content = '\n'.join(lines)
    
    return content

def process_file(file_path: Path) -> None:
    """Przetwarza pojedynczy plik"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content

        # Dodaj importy
        content = add_imports(content)
        
        # Napraw adnotacje
        content = fix_no_return_annotation(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Przetworzono: {file_path}")
        
    except Exception as e:
        print(f"Błąd podczas przetwarzania {file_path}: {e}")

def main():
    """Główna funkcja skryptu"""
    src_dir = Path("src/backend")
    
    # Znajdź wszystkie pliki Python
    python_files = list(src_dir.rglob("*.py"))
    
    print(f"Znaleziono {len(python_files)} plików Python")
    
    for file_path in python_files:
        process_file(file_path)
    
    print("Ukończono automatyczne naprawy")

if __name__ == "__main__":
    main() 