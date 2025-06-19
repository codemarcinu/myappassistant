#!/usr/bin/env python3
import os

ROOT = os.path.abspath(os.path.dirname(__file__))

# Plik ze strukturą drzewa
with open("project_tree.txt", "w", encoding="utf-8") as tree_file:
    for root, dirs, files in os.walk(ROOT):
        level = root.replace(ROOT, '').count(os.sep)
        indent = ' ' * 4 * level
        tree_file.write(f"{indent}{os.path.basename(root)}/\n")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            tree_file.write(f"{subindent}{f}\n")

# Plik z najważniejszymi plikami
important_ext = (".py", ".md", ".txt", ".json")
with open("important_files.txt", "w", encoding="utf-8") as imp_file:
    for root, dirs, files in os.walk(ROOT):
        for f in files:
            if f.endswith(important_ext):
                imp_file.write(os.path.join(root, f) + "\n")
