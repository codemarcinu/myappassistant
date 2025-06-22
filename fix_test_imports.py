#!/usr/bin/env python3
"""
Skrypt do naprawy importów w testach FoodSave AI.
Ten skrypt pomaga zidentyfikować i naprawić problemy z importami w testach.
"""

import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Any


def check_import(module_path, item_name=None):
    """Sprawdza czy można zaimportować moduł lub element z modułu."""
    try:
        if item_name:
            module = importlib.import_module(module_path)
            if hasattr(module, item_name):
                return True, f"✅ {module_path}.{item_name} - OK"
            else:
                return False, f"❌ {module_path}.{item_name} - nie istnieje"
        else:
            importlib.import_module(module_path)
            return True, f"✅ {module_path} - OK"
    except ImportError as e:
        return False, f"❌ {module_path} - ImportError: {e}"
    except Exception as e:
        return False, f"❌ {module_path} - Error: {e}"


def find_imports_in_file(file_path):
    """Znajduje wszystkie importy w pliku."""
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                imports.append((line_num, line))
    except Exception as e:
        print(f"Błąd czytania pliku {file_path}: {e}")

    return imports


def check_test_file_imports(test_file):
    """Sprawdza importy w pliku testowym."""
    print(f"\n🔍 Sprawdzanie importów w: {test_file}")
    print("=" * 60)

    if not Path(test_file).exists():
        print(f"❌ Plik nie istnieje: {test_file}")
        return

    imports = find_imports_in_file(test_file)

    if not imports:
        print("ℹ️  Nie znaleziono importów w pliku")
        return

    for line_num, import_line in imports:
        print(f"Linia {line_num}: {import_line}")

        # Próbuj przeanalizować import
        if import_line.startswith("from "):
            # from module import item
            parts = import_line[5:].split(" import ")
            if len(parts) == 2:
                module_path = parts[0].strip()
                items = [item.strip() for item in parts[1].split(",")]

                for item in items:
                    # Usuń komentarze i aliasy
                    item = item.split(" as ")[0].split(" #")[0].strip()
                    success, message = check_import(module_path, item)
                    print(f"  {message}")
        elif import_line.startswith("import "):
            # import module
            module_path = import_line[7:].strip()
            success, message = check_import(module_path)
            print(f"  {message}")


def scan_directory_for_imports(
    directory_path: str, pattern: str = "*.py"
) -> Dict[str, List[Tuple[int, str]]]:
    """
    Przeszukuje katalog w poszukiwaniu plików Python i zbiera informacje o importach.

    Args:
        directory_path: Ścieżka do katalogu do przeszukania
        pattern: Wzorzec plików do przeszukania

    Returns:
        Słownik z ścieżkami plików jako kluczami i listami importów jako wartościami
    """
    import_map = {}

    for path in Path(directory_path).rglob(pattern):
        if path.is_file():
            imports = find_imports_in_file(str(path))
            if imports:
                import_map[str(path)] = imports

    return import_map


def check_import_structure_compatibility(directory_path: str = "src") -> Dict[str, Any]:
    """
    Sprawdza kompatybilność struktury importów w projekcie.

    Args:
        directory_path: Ścieżka do katalogu głównego projektu

    Returns:
        Słownik z informacjami o kompatybilności importów
    """
    print(f"\n🔍 Sprawdzanie kompatybilności struktury importów w {directory_path}")
    print("=" * 60)

    import_map = scan_directory_for_imports(directory_path)

    stats: Dict[str, Any] = {
        "total_files": len(import_map),
        "total_imports": sum(len(imports) for imports in import_map.values()),
        "src_backend_imports": 0,
        "backend_imports": 0,
        "other_imports": 0,
        "problematic_files": [],
    }

    for file_path, imports in import_map.items():
        file_has_src_backend = False
        file_has_backend = False

        for _, import_line in imports:
            if "from src.backend" in import_line or "import src.backend" in import_line:
                stats["src_backend_imports"] += 1
                file_has_src_backend = True
            elif "from backend" in import_line or "import backend" in import_line:
                stats["backend_imports"] += 1
                file_has_backend = True
            else:
                stats["other_imports"] += 1

        # Jeśli plik ma mieszane importy, oznacz go jako problematyczny
        if file_has_src_backend and file_has_backend:
            stats["problematic_files"].append(file_path)

    return stats


def generate_import_compatibility_report(stats: Dict[str, Any]) -> str:
    """
    Generuje raport kompatybilności importów na podstawie statystyk.

    Args:
        stats: Słownik ze statystykami importów

    Returns:
        Tekst raportu
    """
    report = [
        "\n📊 RAPORT KOMPATYBILNOŚCI IMPORTÓW",
        "=" * 60,
        f"Przeanalizowano plików: {stats['total_files']}",
        f"Łączna liczba importów: {stats['total_imports']}",
        f"Importy typu 'src.backend': {stats['src_backend_imports']}",
        f"Importy typu 'backend': {stats['backend_imports']}",
        f"Inne importy: {stats['other_imports']}",
        "\nWnioski:",
    ]

    # Analiza wyników
    if stats["src_backend_imports"] > 0 and stats["backend_imports"] == 0:
        report.append("✅ Projekt używa konsekwentnie importów typu 'src.backend'.")
        report.append(
            "   Zalecenie: Dostosuj strukturę kontenerów do struktury kodu (Opcja 1)."
        )
    elif stats["src_backend_imports"] == 0 and stats["backend_imports"] > 0:
        report.append("✅ Projekt używa konsekwentnie importów typu 'backend'.")
        report.append(
            "   Zalecenie: Dostosuj importy w kodzie do struktury kontenerów (Opcja 2)."
        )
    elif stats["src_backend_imports"] > 0 and stats["backend_imports"] > 0:
        report.append("⚠️ Projekt używa mieszanej struktury importów!")
        report.append("   Zalecenie: Ujednolicić importy w całym projekcie.")
        if stats["src_backend_imports"] > stats["backend_imports"]:
            report.append(
                "   Sugerowana strategia: Przekształć wszystkie importy na typ 'src.backend'."
            )
        else:
            report.append(
                "   Sugerowana strategia: Przekształć wszystkie importy na typ 'backend'."
            )
    else:
        report.append("ℹ️ Nie znaleziono importów związanych z modułem backend.")

    # Problematyczne pliki
    if stats["problematic_files"]:
        report.append("\nPliki z mieszanymi importami:")
        for file in stats["problematic_files"]:
            report.append(f"- {file}")

    return "\n".join(report)


def main():
    """Główna funkcja skryptu."""
    print("🔧 Skrypt naprawy importów w testach FoodSave AI")
    print("=" * 60)

    # Lista plików testowych do sprawdzenia
    test_files = [
        "tests/test_weather_agent_fixed.py",
        "tests/test_rag_system_fixed.py",
        "tests/test_receipt_processing_fixed.py",
        "tests/test_shopping_conversation_fixed.py",
        "tests/test_orchestrator.py",
    ]

    # Sprawdź każdy plik testowy
    for test_file in test_files:
        check_test_file_imports(test_file)

    # Sprawdź kompatybilność struktury importów w projekcie
    stats = check_import_structure_compatibility()
    report = generate_import_compatibility_report(stats)
    print(report)

    print("\n" + "=" * 60)
    print("📋 Rekomendacje:")
    print("1. Sprawdź rzeczywiste nazwy funkcji/klas w plikach implementacji")
    print("2. Zaktualizuj importy w testach zgodnie z rzeczywistą strukturą")
    print("3. Dostosuj mocki do rzeczywistych interfejsów")
    print("4. Uruchom testy ponownie po naprawie importów")

    print("\n🔗 Przydatne pliki do sprawdzenia:")
    print("- src/backend/api/v2/endpoints/receipts.py")
    print("- src/backend/agents/weather_agent.py")
    print("- src/backend/agents/rag_agent.py")
    print("- src/backend/agents/orchestrator.py")
    print("- src/backend/services/shopping_service.py")


if __name__ == "__main__":
    main()
