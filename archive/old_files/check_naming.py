#!/usr/bin/env python3
import ast
from pathlib import Path


def check_naming_conventions(file_path):
    """Check naming conventions in a Python file"""
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "_" in node.name:
                    print(f"Błąd: Klasa {node.name} w {file_path} zawiera podkreślenia")
            elif isinstance(node, ast.FunctionDef):
                if not ("_" in node.name or node.name.islower()):
                    print(
                        f"Błąd: Funkcja {node.name} w {file_path} nie używa snake_case"
                    )
    except Exception as e:
        print(f"Błąd parsowania {file_path}: {e}")


def main():
    """Check all Python files in src/backend"""
    print("Sprawdzanie konwencji nazewnictwa...")

    for py_file in Path("src/backend").rglob("*.py"):
        check_naming_conventions(py_file)

    print("Sprawdzanie zakończone")


if __name__ == "__main__":
    main()
