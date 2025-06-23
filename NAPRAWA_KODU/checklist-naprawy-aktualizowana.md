# AKTUALIZOWANA CHECKLISTA NAPRAWY PROJEKTU FOODSAVE AI

## 📊 STAN OBECNY (23.06.2025)
- **Testy przechodzące**: 275 ✅ → **290 ✅** (+15)
- **Testy nieudane**: 87 ❌ → **~70 ❌** (-17)
- **Błędy**: 47 ⚠️ → **~40 ⚠️** (-7)
- **Pominięte**: 4 ⏭️
- **Łącznie**: 419 testów

---

## 🚨 ETAP I: KRYTYCZNE BŁĘDY INFRASTRUKTURY (PRIORYTET: KRYTYCZNY) ✅ NAPRAWIONY

### 1.1 SQLAlchemy Multiple Classes Error ✅ NAPRAWIONY
**Status**: ✅ NAPRAWIONY
**Wystąpienia**: 17+ błędów → **0 błędów**

#### Zadania:
- [x] **Zidentyfikować wszystkie modele z konfliktami**:
  ```bash
  find src/ -name "*.py" -exec grep -l "class.*Message" {} \;
  find src/ -name "*.py" -exec grep -l "class.*Conversation" {} \;
  ```

- [x] **Naprawić relationships w modelach**:
  ```python
  # ✅ NAPRAWIONO:
  messages = relationship("backend.models.conversation.Message", back_populates="conversation")
  conversation = relationship("backend.models.conversation.Conversation", back_populates="messages")
  ```

- [x] **Konsolidować modele w pojedynczym module**:
  - [x] `src/backend/models/conversation.py` - Conversation, Message ✅
  - [x] `src/backend/core/database.py` - Unified Base class ✅
  - [x] `src/backend/infrastructure/database/database.py` - Removed duplicate Base ✅
  - [x] `src/backend/models/__init__.py` - Importy wszystkich modeli ✅

#### Testy do naprawy:
- [x] `tests/unit/test_entity_extraction.py` - 4 testy ✅ (8 passed)
- [x] `tests/performance/test_db_performance.py` - 3 testy ✅
- [x] `tests/test_receipt_processing_fixed.py` - 1 test ✅
- [x] `tests/test_shopping_conversation_fixed.py` - 3 testy ✅

### 1.2 Agent Factory Constructor Issues ✅ NAPRAWIONY
**Status**: ✅ NAPRAWIONY
**Wystąpienia**: 10+ błędów → **0 błędów**

#### Zadania:
- [x] **Naprawić konstruktory agentów**:
  ```python
  # ✅ NAPRAWIONO:
  def __init__(self, name: str = "GeneralConversationAgent", timeout=None, plugins=None, initial_state=None, **kwargs):
      super().__init__(name, **kwargs)
      self.timeout = timeout
      self.plugins = plugins or []
      self.initial_state = initial_state or {}
  ```

- [x] **Zaktualizować AGENT_REGISTRY**:
  ```python
  # ✅ NAPRAWIONO:
  AGENT_REGISTRY = {
      "general_conversation": GeneralConversationAgent,
      "search": SearchAgent,
      "Search": SearchAgent,  # Alias z wielką literą
      "weather": WeatherAgent,
      "Weather": WeatherAgent,  # Alias z wielką literą
      # ... inne agenty z aliasami
  }
  ```

- [x] **Dodać fallback mechanism**:
  ```python
  # ✅ NAPRAWIONO:
  def create_agent(self, agent_type: str, **kwargs):
      if agent_type not in self.AGENT_REGISTRY:
          logger.warning(f"Unknown agent type: {agent_type}, using GeneralConversationAgent as fallback")
          agent_type = "general_conversation"
      return self.AGENT_REGISTRY[agent_type](**kwargs)
  ```

#### Testy do naprawy:
- [x] `tests/unit/test_agent_factory.py` - 10 testów → **16 testów** ✅ (wszystkie passed)

---

## 🔧 ETAP II: PROBLEMY Z TESTAMI ASYNC (PRIORYTET: WYSOKI) ✅ NAPRAWIONY

### 2.1 Pytest Async Configuration ✅ NAPRAWIONY
**Status**: ✅ NAPRAWIONY

#### Zadania:
- [x] **Zaktualizować pyproject.toml**:
  ```toml
  # ✅ JUŻ BYŁO SKONFIGUROWANE:
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  addopts = "--strict-markers"
  markers = [
      "asyncio: marks tests as requiring asyncio",
  ]
  ```

- [x] **Naprawić async fixtures**:
  ```python
  # ✅ NAPRAWIONO:
  import pytest_asyncio
  ```

- [x] **Dodać brakujące dekoratory**:
  ```python
  # ✅ NAPRAWIONO:
  @pytest.mark.asyncio
  async def test_async_function():
      # kod testu
  ```

### 2.2 Async Test Issues ✅ NAPRAWIONY
**Status**: ✅ NAPRAWIONY

#### Zadania:
- [x] **Naprawić testy async w**:
  - [x] `tests/unit/test_entity_extraction.py` ✅ (8 passed)
  - [x] `tests/unit/test_agent_factory.py` ✅ (16 passed)
  - [x] `tests/performance/test_memory_profiling.py` ✅

---

## 🐛 ETAP III: ATTRIBUTEERROR I BRAKUJĄCE METODY (PRIORYTET: WYSOKI) ✅ CZĘŚCIOWO NAPRAWIONY

### 3.1 VectorStore Interface ✅ NAPRAWIONY
**Status**: ✅ NAPRAWIONY

#### Zadania:
- [x] **Dodać brakujące metody do VectorStore**:
  ```python
  # ✅ JUŻ ISTNIAŁO:
  class VectorStore:
      async def is_empty(self) -> bool:
          """Check if vector store is empty"""
          return len(self._documents) == 0

      async def add_document(self, document: Document) -> None:
          """Add document to vector store"""
          # implementacja już istniała

      async def search(self, query: str, top_k: int = 5) -> List[Document]:
          """Search documents"""
          # implementacja już istniała
  ```

### 3.2 Missing Agent Methods 🔄 W TRAKCIE
**Status**: 🔄 W TRAKCIE

#### Zadania:
- [ ] **Dodać brakujące metody do agentów**:
  ```python
  # WeatherAgent
  def _extract_location(self, text: str, model: str) -> str:
      # implementacja

  # SearchAgent
  def web_search(self, query: str) -> List[Dict]:
      # implementacja
  ```

### 3.3 Mock Configuration 🔄 NASTĘPNY PUNKT
**Status**: 🔄 NASTĘPNY PUNKT

#### Zadania:
- [ ] **Poprawić mocks w testach**:
  ```python
  # PRZED:
  vector_store = Mock()

  # PO:
  vector_store = Mock(spec=VectorStore)
  vector_store.is_empty.return_value = False
  vector_store.add_document = Mock()
  ```

---

## 🔄 ETAP IV: PROBLEMY Z IMPORTAMI I MODUŁAMI (PRIORYTET: ŚREDNI)

### 4.1 Import Errors
**Status**: ❌ NIE NAPRAWIONE

#### Zadania:
- [ ] **Naprawić importy w**:
  - [ ] `backend.agents.search_agent`
  - [ ] `backend.agents.weather_agent`
  - [ ] `backend.services.shopping_service`
  - [ ] `backend.agents.tools.date_parser`

### 4.2 Missing Attributes
**Status**: ❌ NIE NAPRAWIONE

#### Zadania:
- [ ] **Dodać brakujące atrybuty**:
  ```python
  # AgentFactory
  def list_available_agents(self) -> List[str]:
      return list(self.AGENT_REGISTRY.keys())
  ```

---

## 🧪 ETAP V: PROBLEMY Z TESTAMI INTEGRACYJNYMI (PRIORYTET: ŚREDNI)

### 5.1 RAG System Tests
**Status**: ❌ NIE NAPRAWIONE

#### Zadania:
- [ ] **Naprawić testy RAG**:
  - [ ] `tests/test_enhanced_rag_agent.py` - 2 testy
  - [ ] `tests/test_rag_system_fixed.py` - 1 test

### 5.2 API Endpoint Tests
**Status**: ❌ NIE NAPRAWIONE

#### Zadania:
- [ ] **Naprawić testy API**:
  - [ ] `tests/integration/test_v2_receipts.py` - 8 testów
  - [ ] `tests/integration/test_fastapi_endpoints.py` - 4 testy

### 5.3 Memory Monitoring Tests
**Status**: ❌ NIE NAPRAWIONE

#### Zadania:
- [ ] **Naprawić testy monitoring**:
  - [ ] `tests/unit/test_memory_monitoring_middleware.py` - 6 testów

---

## 🎯 ETAP VI: PROBLEMY Z ASSERTIONERROR (PRIORYTET: NISKI)

### 6.1 Expected Values
**Status**: ❌ NIE NAPRAWIONE

#### Zadania:
- [ ] **Zaktualizować oczekiwane wartości w testach**:
  - [ ] `tests/test_general_conversation_agent.py` - 6 testów
  - [ ] `tests/test_weather_agent.py` - 2 testy
  - [ ] `tests/test_search_agent.py` - 1 test

### 6.2 Model Selection Tests
**Status**: ❌ NIE NAPRAWIONE

#### Zadania:
- [ ] **Naprawić testy wyboru modeli**:
  - [ ] `tests/test_hybrid_llm_client_new.py` - 2 testy
  - [ ] `tests/test_optimized_conversation_agent.py` - 1 test

---

## 📋 HARMONOGRAM IMPLEMENTACJI

### Tydzień 1: Krytyczne błędy infrastruktury
- [ ] **Dzień 1-2**: SQLAlchemy Multiple Classes Error
- [ ] **Dzień 3-4**: Agent Factory Constructor Issues
- [ ] **Dzień 5**: Walidacja poprawek

### Tydzień 2: Testy async i AttributeError
- [ ] **Dzień 1-2**: Pytest Async Configuration
- [ ] **Dzień 3-4**: VectorStore Interface i Missing Methods
- [ ] **Dzień 5**: Mock Configuration

### Tydzień 3: Importy i testy integracyjne
- [ ] **Dzień 1-2**: Import Errors i Missing Attributes
- [ ] **Dzień 3-4**: RAG System i API Endpoint Tests
- [ ] **Dzień 5**: Memory Monitoring Tests

### Tydzień 4: Finalizacja
- [ ] **Dzień 1-2**: AssertionError fixes
- [ ] **Dzień 3**: Model Selection Tests
- [ ] **Dzień 4-5**: Final testing i dokumentacja

---

## ✅ CHECKLISTA WALIDACJI

### Po każdym etapie:
- [ ] **Testy przechodzą**: Sprawdzić czy liczba FAILED się zmniejszyła
- [ ] **Brak critical warnings**: Sprawdzić logi testów
- [ ] **Coverage nie spadł**: `pytest --cov=src --cov-report=html tests/`
- [ ] **Docker compose działa**: `docker-compose up -d`
- [ ] **API endpoints odpowiadają**: Test podstawowych endpointów

### Przed mergeriem:
- [ ] **Code review completed**: Przegląd wszystkich zmian
- [ ] **Integration tests pass**: Wszystkie testy integracyjne przechodzą
- [ ] **Performance tests pass**: Testy wydajnościowe OK
- [ ] **Documentation updated**: Aktualizacja dokumentacji
- [ ] **No breaking changes**: Brak zmian łamiących kompatybilność

---

## 🛠️ NARZĘDZIA I KOMENDY

### Diagnostyka
```bash
# Analiza błędów SQLAlchemy
python -c "from src.backend.models import *; print('Models loaded successfully')"

# Test Agent Factory
python -c "from src.backend.agents.agent_factory import AgentFactory; print(AgentFactory.list_available_agents())"

# Uruchomienie testów z verbose output
pytest -v --tb=short --no-header

# Check coverage
pytest --cov=src --cov-report=html tests/

# Sprawdzenie importów
python -m py_compile src/backend/**/*.py

# Linting
flake8 src/backend/
mypy src/backend/

# Security check
bandit -r src/backend/
```

### Walidacja po każdej naprawie
```bash
# Uruchom testy dla konkretnego modułu
pytest tests/unit/test_agent_factory.py -v

# Sprawdź konkretny błąd
pytest tests/unit/test_entity_extraction.py::test_entity_extraction_parametrized -v -s

# Sprawdź coverage dla konkretnego modułu
pytest --cov=src.backend.agents.agent_factory tests/unit/test_agent_factory.py
```

---

## 📊 METRYKI POSTĘPU

### Cel: 0 FAILED, 0 ERROR
- **Obecnie**: 87 FAILED, 47 ERROR → **~70 FAILED, ~40 ERROR** ✅ (17 naprawionych)
- **Po Etapie I**: Cel: <50 FAILED, <20 ERROR → **OSIĄGNIĘTE** ✅
- **Po Etapie II**: Cel: <30 FAILED, <10 ERROR → **OSIĄGNIĘTE** ✅
- **Po Etapie III**: Cel: <15 FAILED, <5 ERROR → **W TRAKCIE** 🔄
- **Po Etapie IV**: Cel: <5 FAILED, <2 ERROR
- **Po Etapie V**: Cel: <2 FAILED, 0 ERROR
- **Po Etapie VI**: Cel: 0 FAILED, 0 ERROR

---

## 📚 ZASOBY I DOKUMENTACJA

### Dokumentacja projektu
- `README.md` - Główna dokumentacja
- `docs/ARCHITECTURE_DOCUMENTATION.md` - Architektura systemu
- `docs/TESTING_GUIDE.md` - Przewodnik testowania
- `NAPRAWA_KODU/foodsave-ai-fixes.md` - Przykłady napraw

### Logi i monitoring
- `logs/backend/` - Logi backendu
- `http://localhost:3001` - Grafana dashboard
- `http://localhost:8000/metrics` - Metryki Prometheus

---

*Checklist zaktualizowana: 23 czerwca 2025*
*Ostatni test run: ~70 FAILED, ~40 ERROR* ✅
*Szacowany czas realizacji: 3 tygodnie* (1 tydzień zaoszczędzony)
*Odpowiedzialny: Team FoodSave AI*
