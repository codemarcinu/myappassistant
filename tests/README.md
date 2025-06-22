# FoodSave AI - System testów

Ten katalog zawiera testy dla systemu FoodSave AI. Testy są podzielone na następujące kategorie:

## Kategorie testów

### 1. Testy jednostkowe (unit)
Testy jednostkowe sprawdzają pojedyncze komponenty systemu w izolacji od innych komponentów. Znajdują się w katalogu `src/backend/tests/unit/`.

### 2. Testy agentów (agents)
Testy sprawdzające działanie poszczególnych agentów AI, takich jak:
- SearchAgent - wyszukiwanie w internecie
- WeatherAgent - prognozy pogody
- OCRAgent - rozpoznawanie tekstu z obrazów
- RAGAgent - system RAG (Retrieval-Augmented Generation)
- ChefAgent - agent do przepisów kulinarnych
- MealPlannerAgent - agent do planowania posiłków

### 3. Testy integracyjne (integration)
Testy sprawdzające współpracę pomiędzy różnymi komponentami systemu, w tym:
- Orchestrator - koordynacja pracy agentów
- Przetwarzanie paragonów
- Konwersacje związane z zakupami

### 4. Testy wydajnościowe (performance)
Testy sprawdzające wydajność systemu, w tym:
- Wydajność bazy danych
- Profilowanie pamięci

### 5. Poprawione testy (fixed)
Poprawione wersje testów, które zostały dostosowane do aktualnej implementacji:
- test_search_agent_fixed.py
- test_weather_agent_fixed.py
- test_rag_system_fixed.py
- test_receipt_processing_fixed.py
- test_shopping_conversation_fixed.py
- test_orchestrator.py

## Uruchamianie testów

Testy można uruchamiać za pomocą skryptu `run_foodsave_tests.py` znajdującego się w głównym katalogu projektu.

### Przykłady użycia:

1. Wyświetlenie dostępnych kategorii testów:
```bash
./run_foodsave_tests.py --list
```

2. Wyświetlenie wszystkich testów:
```bash
./run_foodsave_tests.py --list-tests
```

3. Wyświetlenie testów w określonej kategorii:
```bash
./run_foodsave_tests.py --list-category agents
```

4. Uruchomienie testów z określonej kategorii:
```bash
./run_foodsave_tests.py agents
```

5. Uruchomienie wszystkich testów:
```bash
./run_foodsave_tests.py all
```

6. Uruchomienie testów w trybie szczegółowym:
```bash
./run_foodsave_tests.py agents -v
```

## Struktura testów

Każdy test jest zaprojektowany tak, aby sprawdzać określoną funkcjonalność systemu. Testy używają biblioteki `pytest` i są asynchroniczne, co pozwala na testowanie asynchronicznych funkcji używanych w systemie.

### Przykładowa struktura testu:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_some_functionality():
    # Arrange - przygotowanie danych testowych
    ...
    
    # Act - wywołanie testowanej funkcji
    ...
    
    # Assert - sprawdzenie wyników
    assert result.success is True
    assert "expected text" in result.text
```

## Mockowanie zależności

Większość testów używa mocków do izolowania testowanego komponentu od jego zależności. Używamy do tego biblioteki `unittest.mock`, która pozwala na tworzenie mocków i szpiegów.

### Przykład mockowania:

```python
# Mock dla bazy danych
mock_db = AsyncMock()

# Mock dla agenta
mock_agent = MagicMock()
mock_agent.process = AsyncMock(return_value=AgentResponse(...))

# Mock dla klienta LLM
with patch("backend.core.hybrid_llm_client.hybrid_llm_client.chat") as mock_chat:
    mock_chat.return_value = {"message": {"content": "Odpowiedź modelu"}}
    
    # Test z użyciem mocka
    result = await function_under_test(...)
```

## Dodawanie nowych testów

Podczas dodawania nowych testów należy:

1. Umieścić test w odpowiednim katalogu
2. Nazwać plik zgodnie z konwencją `test_*.py`
3. Dodać test do odpowiedniej kategorii w skrypcie `run_foodsave_tests.py`
4. Upewnić się, że test jest asynchroniczny, jeśli testuje asynchroniczne funkcje
5. Używać mocków do izolowania testowanego komponentu
6. Dodać odpowiednie asercje sprawdzające wyniki 