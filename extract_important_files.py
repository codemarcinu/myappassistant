#!/usr/bin/env python3
import os

ROOT = os.path.abspath(os.path.dirname(__file__))

# Lista najważniejszych plików i katalogów do analizy
important_paths = [
    "pyproject.toml",
    "poetry.lock",
    "requirements-fix.txt",
    ".pre-commit-config.yaml",
    ".gitignore",
    ".flake8",
    ".mypy.ini",
    "docker-compose.yaml",
    "dockerfile",
    "README.md",
    "GPU_SETUP.md",
    "LICENSE",
    "REFACTORING_PLAN.md",
    "src/__init__.py",
    "src/backend/main.py",
    "src/backend/config.py",
    "src/backend/run_intent_tests.py",
    "src/backend/debug_imports.py",
    "src/backend/ml_training/intent_trainer.py",
    "src/backend/integrations/web_search.py",
    "src/backend/schemas/shopping_schemas.py",
    "src/backend/core/",
    "src/backend/tests/",
    "src/backend/api/",
    "src/services/shopping_service.py",
    "src/orchestrator_management/request_queue.py",
    "src/orchestrator_management/orchestrator_pool.py",
    "src/domain/repositories.py",
    "src/models/conversation.py",
    "src/models/user_profile.py",
    "src/models/shopping.py",
    "src/application/use_cases/process_query_use_case.py",
    "src/agents/",
    "src/infrastructure/",
]

def collect_files(paths):
    files = []
    for path in paths:
        full_path = os.path.join(ROOT, path)
        if os.path.isdir(full_path):
            for dirpath, _, filenames in os.walk(full_path):
                for f in filenames:
                    if f.endswith('.py') or f.endswith('.md') or f.endswith('.toml') or f.endswith('.yaml') or f.endswith('.yml') or f.endswith('.txt'):
                        files.append(os.path.relpath(os.path.join(dirpath, f), ROOT))
        elif os.path.isfile(full_path):
            files.append(path)
    return files

important_files = collect_files(important_paths)

with open("important_files.txt", "w", encoding="utf-8") as f:
    for file in important_files:
        f.write(file + "\n")
