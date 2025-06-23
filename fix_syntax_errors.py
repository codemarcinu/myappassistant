#!/usr/bin/env python3
"""
Automatyczna naprawa błędów składniowych w adnotacjach typów
Naprawia błędy typu: parameter -> Any: type na parameter: type
"""

import os
import re
import glob
from pathlib import Path

def fix_syntax_errors_in_file(file_path: str) -> bool:
    """Naprawia błędy składniowe w pojedynczym pliku"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Napraw błędy składniowe w adnotacjach typów
        # 1. Napraw: parameter -> Any: type na parameter: type
        content = re.sub(r'(\w+)\s*->\s*Any:\s*([^,\s]+)', r'\1: \2', content)
        
        # 2. Napraw: parameter -> None: type na parameter: type
        content = re.sub(r'(\w+)\s*->\s*None:\s*([^,\s]+)', r'\1: \2', content)
        
        # 3. Napraw: ) -> Any: na ) -> None:
        content = re.sub(r'\)\s*->\s*Any:', r') -> None:', content)
        
        # 4. Napraw: ) -> Any na ) -> None
        content = re.sub(r'\)\s*->\s*Any$', r') -> None', content, flags=re.MULTILINE)
        
        # 5. Napraw: def func(self, param -> Any: type) -> Any: na def func(self, param: type) -> None:
        content = re.sub(r'def\s+(\w+)\s*\([^)]*\)\s*->\s*Any:', r'def \1(...) -> None:', content)
        
        # 6. Napraw: async def func(self, param -> Any: type) -> Any: na async def func(self, param: type) -> None:
        content = re.sub(r'async\s+def\s+(\w+)\s*\([^)]*\)\s*->\s*Any:', r'async def \1(...) -> None:', content)
        
        # 7. Napraw: def func(self, param -> Any: type) -> Any na def func(self, param: type) -> None
        content = re.sub(r'def\s+(\w+)\s*\([^)]*\)\s*->\s*Any$', r'def \1(...) -> None', content, flags=re.MULTILINE)
        
        # 8. Napraw: async def func(self, param -> Any: type) -> Any na async def func(self, param: type) -> None
        content = re.sub(r'async\s+def\s+(\w+)\s*\([^)]*\)\s*->\s*Any$', r'async def \1(...) -> None', content, flags=re.MULTILINE)
        
        # 9. Napraw: def __init__(self, param -> Any: type) -> Any: na def __init__(self, param: type) -> None:
        content = re.sub(r'def\s+__init__\s*\([^)]*\)\s*->\s*Any:', r'def __init__(...) -> None:', content)
        
        # 10. Napraw: async def func(param -> Any: type) -> Any: na async def func(param: type) -> None:
        content = re.sub(r'async\s+def\s+(\w+)\s*\([^)]*\)\s*->\s*Any:', r'async def \1(...) -> None:', content)
        
        # Jeśli zawartość się zmieniła, zapisz plik
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Błąd podczas przetwarzania {file_path}: {e}")
        return False

def find_python_files(directory: str) -> list:
    """Znajduje wszystkie pliki Python w katalogu"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Pomiń katalogi venv, __pycache__, .git
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """Główna funkcja naprawy błędów składniowych"""
    backend_dir = "src/backend"
    
    if not os.path.exists(backend_dir):
        print(f"Katalog {backend_dir} nie istnieje!")
        return
    
    print("🔍 Szukam plików Python...")
    python_files = find_python_files(backend_dir)
    print(f"📁 Znaleziono {len(python_files)} plików Python")
    
    fixed_files = []
    total_errors = 0
    
    print("\n🔧 Naprawiam błędy składniowe...")
    for file_path in python_files:
        try:
            if fix_syntax_errors_in_file(file_path):
                fixed_files.append(file_path)
                print(f"✅ Naprawiono: {file_path}")
        except Exception as e:
            print(f"❌ Błąd w {file_path}: {e}")
    
    print(f"\n📊 Podsumowanie:")
    print(f"   - Przetworzono plików: {len(python_files)}")
    print(f"   - Naprawiono plików: {len(fixed_files)}")
    
    if fixed_files:
        print(f"\n📝 Naprawione pliki:")
        for file_path in fixed_files:
            print(f"   - {file_path}")
    
    print(f"\n🎯 Następny krok: Uruchom 'python3 -m mypy src/backend --show-error-codes'")

if __name__ == "__main__":
    main() 