# Naming Conventions Refactoring Plan

## Current to Proposed Name Mappings

### Agent Classes
- `enhanced_orchestrator.py` → `orchestrator.py`
  - `EnhancedOrchestrator` → `Orchestrator`
- `enhanced_base_agent.py` → `base_agent.py`
  - `EnhancedBaseAgent` → `BaseAgent`
  - `EnhancedAgentResponse` → `AgentResponse`
- `enhanced_weather_agent.py` → `weather_agent.py`
  - `EnhancedWeatherAgent` → `WeatherAgent`
- `enhanced_rag_agent.py` → `rag_agent.py`
  - `EnhancedRAGAgent` → `RAGAgent`

### Core Components
- `enhanced_vector_store.py` → `vector_store.py`
  - `EnhancedVectorStore` → `VectorStore`
  - `enhanced_vector_store` → `vector_store`

### Variables/Methods
- `new_data` → `data` (when scope is clear)
- `old_chunks` → `stale_chunks` or `expired_chunks`
- `temp_` prefixes → remove when possible
- `improved_` prefixes → remove when possible

## Implementation Steps

1. Update file names first
2. Update class names and imports
3. Update variable/method names
4. Update tests and documentation
5. Verify all references are updated

## Verification

Run these commands after changes:
```bash
# Check naming conventions
python -c "
import ast
import os
from pathlib import Path

def check_naming(file_path):
    with open(file_path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            assert '_' not in node.name, f'Class {node.name} contains underscores'
        elif isinstance(node, ast.FunctionDef):
            assert node.name.islower() or '_' in node.name, f'Function {node.name} should be snake_case'

for py_file in Path('src/backend').rglob('*.py'):
    check_naming(py_file)
"

# Check for remaining old names
grep -r "enhanced_\|improved_\|new_\|old_\|temp_" src/
