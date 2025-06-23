# Kompleksowy Plan Naprawy Projektu FoodSave AI

## 1. ANALIZA STANU OBECNEGO

### Zidentyfikowane Główne Problemy
- **AttributeError (59 wystąpień)** - głównie VectorStore.is_empty, problemy z API obiektów
- **Unsupported Agent Type (24 wystąpienia)** - problemy z Agent Factory
- **AssertionError (22 wystąpienia)** - testy nie przechodzą z oczekiwanymi wartościami
- **SQLAlchemy Mapper Initialization (17 wystąpień)** - problemy z mapperami bazy danych
- **Async Function Support (5 wystąpień)** - problemy z testami async
- **SQLAlchemy Multiple Classes (4 wystąpienia)** - konflikty klas w rejestrze

---

## 2. PLAN NAPRAWY - ETAP I: KRYTYCZNE BŁĘDY INFRASTRUKTURY

### 2.1 Naprawa SQLAlchemy Multiple Classes Error

**Priorytet: KRYTYCZNY**

**Problem**: Konflikt klas "Message" w rejestrze SQLAlchemy
```
Multiple classes found for path "Message" in the registry of this declarative base.
Please use a fully module-qualified path.
```

**Rozwiązanie**:
1. **Zidentyfikować wszystkie modele SQLAlchemy z conflictami**:
   ```bash
   find src/ -name "*.py" -exec grep -l "class.*Message" {} \;
   find src/ -name "*.py" -exec grep -l "class.*Conversation" {} \;
   ```

2. **Zastąpić string-based relationships pełnymi ścieżkami**:
   ```python
   # PRZED (błędne):
   messages = relationship("Message", back_populates="conversation")

   # PO (poprawne):
   messages = relationship("src.backend.models.conversation.Message", back_populates="conversation")
   ```

3. **Konsolidować modele w pojedynczym module**:
   ```
   src/backend/models/
   ├── __init__.py         # Importy wszystkich modeli
   ├── base.py            # Base class
   ├── conversation.py    # Conversation, Message
   ├── shopping.py        # Purchase, Item
   └── user.py           # User-related models
   ```

### 2.2 Naprawa Agent Factory

**Priorytet: KRYTYCZNY**

**Problem**: Unsupported agent types w AgentFactory

**Rozwiązanie**:
1. **Zaktualizować AgentFactory registry**:
   ```python
   # src/backend/agents/agent_factory.py
   AGENT_REGISTRY = {
       "general_conversation": GeneralConversationAgent,
       "shopping_conversation": ShoppingConversationAgent,
       "food_conversation": FoodConversationAgent,
       "information_query": InformationQueryAgent,
       "cooking": CookingAgent,
       "search": SearchAgent,
       "weather": WeatherAgent,
       "rag": RAGAgent,
       "categorization": CategorizationAgent,
       "meal_planning": MealPlannerAgent,
       "ocr": OCRAgent,
       "analytics": AnalyticsAgent,
   }
   ```

2. **Dodać fallback mechanism**:
   ```python
   def create_agent(self, agent_type: str, **kwargs):
       if agent_type not in self.AGENT_REGISTRY:
           logger.warning(f"Unknown agent type: {agent_type}, using GeneralConversationAgent")
           agent_type = "general_conversation"
       return self.AGENT_REGISTRY[agent_type](**kwargs)
   ```

---

## 3. PLAN NAPRAWY - ETAP II: TESTY I FIXTURES

### 3.1 Naprawa Pytest Async Issues

**Priorytet: WYSOKI**

**Problem**: Async functions not natively supported

**Rozwiązanie**:
1. **Dodać pytest-asyncio konfigurację**:
   ```toml
   # pyproject.toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   addopts = "--strict-markers"
   markers = [
       "asyncio: marks tests as requiring asyncio",
   ]
   ```

2. **Poprawić async fixtures**:
   ```python
   # PRZED:
   @pytest.fixture
   async def db_session():
       # kod

   # PO:
   @pytest_asyncio.fixture
   async def db_session():
       # kod
   ```

3. **Dodać brakujące dekoratory**:
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       # kod testu
   ```

### 3.2 Naprawa AttributeError w testach

**Priorytet: WYSOKI**

**Problem**: VectorStore.is_empty i inne missing attributes

**Rozwiązanie**:
1. **Poprawić VectorStore interface**:
   ```python
   # src/backend/core/vector_store.py
   class VectorStore:
       def is_empty(self) -> bool:
           """Check if vector store is empty"""
           return len(self._vectors) == 0

       def add_document(self, document: str) -> None:
           """Add document to vector store"""
           # implementacja
   ```

2. **Zaktualizować mocks w testach**:
   ```python
   # tests/conftest.py
   @pytest.fixture
   def mock_vector_store():
       mock = Mock(spec=VectorStore)
       mock.is_empty.return_value = False
       mock.add_document = Mock()
       return mock
   ```

---

## 4. PLAN NAPRAWY - ETAP III: ARCHITEKTURA I REFAKTORYZACJA

### 4.1 Reorganizacja struktury projektu

**Priorytet: ŚREDNI**

**Cel**: Uporządkowanie importów i zależności

**Akcje**:
1. **Konsolidacja importów**:
   ```python
   # src/backend/__init__.py
   from .models import *
   from .agents import *
   from .core import *
   ```

2. **Rozwiązanie circular imports**:
   - Użycie TYPE_CHECKING
   - Lazy imports
   - Dependency injection

3. **Standaryzacja error handling**:
   ```python
   # src/backend/core/exceptions.py
   class FoodSaveBaseException(Exception):
       """Base exception for FoodSave AI"""

   class AgentError(FoodSaveBaseException):
       """Agent-related errors"""

   class DatabaseError(FoodSaveBaseException):
       """Database-related errors"""
   ```

### 4.2 Ulepszenie systemu agentów

**Priorytet: ŚREDNI**

**Akcje**:
1. **Standaryzacja Agent interfaces**:
   ```python
   # src/backend/agents/base_agent.py
   class BaseAgent(ABC):
       @abstractmethod
       async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
           pass

       @abstractmethod
       def validate_input(self, input_data: Dict[str, Any]) -> bool:
           pass
   ```

2. **Dodanie Agent health checks**:
   ```python
   async def health_check(self) -> bool:
       """Check if agent is healthy and ready"""
       return True
   ```

---

## 5. PLAN NAPRAWY - ETAP IV: MONITORING I JAKOŚĆ

### 5.1 Poprawa coverage testów

**Priorytet: NISKI**

**Cel**: Zwiększenie coverage z 95% do 98%

**Akcje**:
1. **Dodanie brakujących testów dla Agent Factory**
2. **Testy integracyjne dla nowych agentów**
3. **Testy end-to-end dla głównych flows**

### 5.2 Dokumentacja

**Priorytet: NISKI**

**Akcje**:
1. **Aktualizacja API documentation**
2. **Dodanie przykładów użycia agentów**
3. **Troubleshooting guide**

---

## 6. HARMONOGRAM IMPLEMENTACJI

### Tydzień 1: Krytyczne błędy
- [ ] Naprawa SQLAlchemy Multiple Classes (2 dni)
- [ ] Naprawa Agent Factory (2 dni)
- [ ] Testy podstawowej funkcjonalności (1 dzień)

### Tydzień 2: Testy i fixtures
- [ ] Naprawa pytest async issues (2 dni)
- [ ] Naprawa AttributeError w testach (2 dni)
- [ ] Walidacja poprawek (1 dzień)

### Tydzień 3: Refaktoryzacja
- [ ] Reorganizacja struktury projektu (3 dni)
- [ ] Ulepszenie systemu agentów (2 dni)

### Tydzień 4: Finalizacja
- [ ] Monitoring i jakość (2 dni)
- [ ] Dokumentacja (2 dni)
- [ ] Final testing (1 dzień)

---

## 7. CHECKLISTY WALIDACJI

### Po każdym etapie:
- [ ] Wszystkie testy przechodzą
- [ ] Brak critical warnings w logach
- [ ] Coverage nie spadł poniżej obecnego poziomu
- [ ] Docker compose up działa bez błędów
- [ ] API endpoints odpowiadają poprawnie

### Przed mergeriem:
- [ ] Code review completed
- [ ] Integration tests pass
- [ ] Performance tests pass
- [ ] Documentation updated
- [ ] No breaking changes introduced

---

## 8. NARZĘDZIA I KOMENDY

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
```

### Walidacja
```bash
# Sprawdzenie importów
python -m py_compile src/backend/**/*.py

# Linting
flake8 src/backend/
mypy src/backend/

# Security check
bandit -r src/backend/
```

---

## 9. KONTAKTY I ZASOBY

### Dokumentacja projektu
- README.md - Główna dokumentacja
- docs/ARCHITECTURE_DOCUMENTATION.md - Architektura systemu
- docs/TESTING_GUIDE.md - Przewodnik testowania

### Logi i monitoring
- logs/backend/ - Logi backendu
- http://localhost:3001 - Grafana dashboard
- http://localhost:8000/metrics - Metryki Prometheus

---

*Plan stworzony: 23 czerwca 2025*
*Szacowany czas realizacji: 4 tygodnie*
*Odpowiedzialny: Team FoodSave AI*
