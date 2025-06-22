# 🧪 Przewodnik po Testowaniu - FoodSave AI

## 📋 Strategia Testowania

FoodSave AI wykorzystuje kompleksową strategię testowania obejmującą testy jednostkowe, integracyjne, wydajnościowe i end-to-end. System testowania jest zoptymalizowany pod kątem szybkości, niezawodności i pokrycia kodu.

## 🎯 Typy Testów

### 1. Unit Tests (Testy Jednostkowe)

Testy pojedynczych komponentów w izolacji.

**Lokalizacja:** `tests/unit/`

**Przykłady:**
- Testy agentów AI
- Testy serwisów
- Testy modeli danych
- Testy utility functions

### 2. Integration Tests (Testy Integracyjne)

Testy interakcji między komponentami.

**Lokalizacja:** `tests/integration/`

**Przykłady:**
- Testy API endpoints
- Testy komunikacji z bazą danych
- Testy integracji z zewnętrznymi API
- Testy orkiestracji agentów

### 3. Performance Tests (Testy Wydajnościowe)

Testy wydajności i obciążenia.

**Lokalizacja:** `tests/performance/`

**Przykłady:**
- Testy response time
- Testy memory usage
- Load testing
- Stress testing

### 4. E2E Tests (Testy End-to-End)

Testy kompletnych scenariuszy użytkownika.

**Lokalizacja:** `tests/e2e/`

**Przykłady:**
- Testy przepływów użytkownika
- Testy interfejsu użytkownika
- Testy kompletnych funkcjonalności

## 🛠️ Konfiguracja Testów

### Pytest Configuration

```python
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["src"]
markers = [
    "e2e: marks tests as end-to-end",
    "performance: marks tests as performance tests",
    "memory: marks tests as memory profiling tests",
    "slow: marks tests as slow running",
    "integration: marks tests as integration tests",
]

[tool.pytest-benchmark]
min_rounds = 5
max_time = 10.0
warmup = true
```

### Test Dependencies

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-cov = "^4.0"
pytest-asyncio = "^0.20.0"
pytest-benchmark = "^4.0.0"
pytest-mock = "^3.12.0"
pytest-xdist = "^3.5.0"
memory-profiler = "^0.61.0"
memray = "^1.12.0"
locust = "^2.20.0"
```

## 🧪 Przykłady Testów

### 1. Unit Tests - Agent Tests

```python
# tests/unit/test_chef_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from src.backend.agents.chef_agent import ChefAgent

class TestChefAgent:
    """Testy dla Chef Agent"""

    @pytest.fixture
    def mock_llm_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_database(self):
        return AsyncMock()

    @pytest.fixture
    def chef_agent(self, mock_llm_client, mock_database):
        return ChefAgent(mock_llm_client, mock_database)

    @pytest.mark.asyncio
    async def test_recipe_generation(self, chef_agent, mock_llm_client):
        """Test generowania przepisu"""
        # Arrange
        mock_llm_client.chat.return_value = {
            "message": {"content": "Przepis na pizzę: składniki..."}
        }

        # Act
        response = await chef_agent.process("Pokaż mi przepis na pizzę", {})

        # Assert
        assert "pizza" in response.lower()
        assert "składniki" in response.lower()
        mock_llm_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingredient_substitution(self, chef_agent, mock_llm_client):
        """Test sugestii substytutów składników"""
        # Arrange
        mock_llm_client.chat.return_value = {
            "message": {"content": "Możesz zastąpić mleko mlekiem migdałowym..."}
        }

        # Act
        response = await chef_agent.process("Czy mogę zastąpić mleko?", {})

        # Assert
        assert "substytut" in response.lower() or "zastąpić" in response.lower()
        assert "migdałowe" in response.lower()

    @pytest.mark.asyncio
    async def test_error_handling(self, chef_agent, mock_llm_client):
        """Test obsługi błędów"""
        # Arrange
        mock_llm_client.chat.side_effect = Exception("LLM error")

        # Act & Assert
        with pytest.raises(Exception):
            await chef_agent.process("Pokaż mi przepis", {})
```

### 2. Integration Tests - API Tests

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from src.backend.main import app

class TestAPIEndpoints:
    """Testy endpointów API"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_chat_endpoint(self, client):
        """Test endpointu chat"""
        # Arrange
        payload = {
            "message": "Pokaż mi przepis na spaghetti",
            "session_id": "test_session"
        }

        # Act
        response = await client.post("/api/v1/chat", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent_used" in data
        assert "confidence" in data

    @pytest.mark.asyncio
    async def test_upload_receipt_endpoint(self, client):
        """Test endpointu upload receipt"""
        # Arrange
        with open("tests/fixtures/test_receipt.jpg", "rb") as f:
            files = {"file": ("receipt.jpg", f, "image/jpeg")}

            # Act
            response = await client.post("/api/v2/upload/receipt", files=files)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "receipt_id" in data
        assert "items" in data
        assert "total_amount" in data

    @pytest.mark.asyncio
    async def test_weather_endpoint(self, client):
        """Test endpointu weather"""
        # Arrange
        params = {"city": "Warszawa"}

        # Act
        response = await client.get("/api/v2/weather/current", params=params)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "location" in data
        assert "weather" in data
        assert data["location"]["city"] == "Warszawa"
```

### 3. Performance Tests

```python
# tests/performance/test_agent_performance.py
import pytest
import time
from src.backend.agents.chef_agent import ChefAgent

class TestAgentPerformance:
    """Testy wydajności agentów"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_chef_agent_response_time(self, benchmark):
        """Test czasu odpowiedzi Chef Agent"""
        agent = ChefAgent(mock_llm_client, mock_database)

        def process_request():
            return await agent.process("Pokaż mi przepis na pizzę", {})

        # Benchmark
        result = benchmark(process_request)
        assert result is not None

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test użycia pamięci"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform operations
        agent = ChefAgent(mock_llm_client, mock_database)
        for _ in range(100):
            await agent.process("Test message", {})

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Assert memory increase is reasonable (< 100MB)
        assert memory_increase < 100 * 1024 * 1024
```

### 4. E2E Tests

```python
# tests/e2e/test_user_workflows.py
import pytest
from playwright.async_api import async_playwright

class TestUserWorkflows:
    """Testy przepływów użytkownika"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_recipe_search_workflow(self):
        """Test przepływu wyszukiwania przepisu"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to app
            await page.goto("http://localhost:3000")

            # Open chat
            await page.click('[data-testid="chat-button"]')

            # Send message
            await page.fill('[data-testid="message-input"]', "Pokaż mi przepis na pizzę")
            await page.click('[data-testid="send-button"]')

            # Wait for response
            await page.wait_for_selector('[data-testid="assistant-message"]')

            # Verify response contains recipe
            response_text = await page.text_content('[data-testid="assistant-message"]')
            assert "pizza" in response_text.lower()
            assert "składniki" in response_text.lower()

            await browser.close()

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_receipt_upload_workflow(self):
        """Test przepływu uploadu paragonu"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to shopping page
            await page.goto("http://localhost:3000/shopping")

            # Upload receipt
            await page.set_input_files('[data-testid="receipt-upload"]', "tests/fixtures/test_receipt.jpg")

            # Wait for processing
            await page.wait_for_selector('[data-testid="receipt-items"]')

            # Verify items are displayed
            items = await page.query_selector_all('[data-testid="receipt-item"]')
            assert len(items) > 0

            await browser.close()
```

## 🔧 Mocking i Fixtures

### LLM Client Mocking

```python
def make_llm_chat_mock(stream_content: str, non_stream_content: str = None):
    """
    Zwraca funkcję do mockowania llm_client.chat,
    która obsługuje zarówno stream=True (async generator), jak i stream=False (dict).
    """
    async def chat_mock(*args, **kwargs):
        if kwargs.get("stream"):
            async def stream():
                yield {"message": {"content": stream_content}}
            return stream()
        else:
            return {"message": {"content": non_stream_content or stream_content}}
    return chat_mock

# Usage in tests
@patch("src.backend.agents.chef_agent.llm_client", new_callable=AsyncMock)
def test_chef_agent_with_mock(mock_llm_client):
    mock_llm_client.chat = make_llm_chat_mock(
        stream_content="Przepis na pizzę: składniki...",
        non_stream_content="Przepis na pizzę: składniki..."
    )
    # Test implementation...
```

### Database Fixtures

```python
@pytest.fixture
async def test_db():
    """Test database fixture"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    yield TestingSessionLocal

    await engine.dispose()

@pytest.fixture
async def sample_user(test_db):
    """Sample user fixture"""
    async with test_db() as session:
        user = User(
            username="testuser",
            email="test@example.com"
        )
        session.add(user)
        await session.commit()
        yield user
```

## 📊 Coverage i Raporty

### Coverage Configuration

```python
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```

### Running Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test types
pytest tests/unit/ --cov=src.backend.agents
pytest tests/integration/ --cov=src.backend.api
pytest tests/performance/ --benchmark-only

# Generate coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

## 🚀 Load Testing

### Locust Configuration

```python
# locustfile.py
from locust import HttpUser, task, between

class FoodSaveUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def chat_request(self):
        """Simulate chat requests"""
        payload = {
            "message": "Pokaż mi przepis na pizzę",
            "session_id": "load_test_session"
        }
        self.client.post("/api/v1/chat", json=payload)

    @task(1)
    def weather_request(self):
        """Simulate weather requests"""
        self.client.get("/api/v2/weather/current?city=Warszawa")

    @task(1)
    def health_check(self):
        """Simulate health check requests"""
        self.client.get("/health")
```

### Running Load Tests

```bash
# Start Locust
locust -f locustfile.py --host=http://localhost:8000

# Run headless load test
locust -f locustfile.py --host=http://localhost:8000 --headless --users 10 --spawn-rate 2 --run-time 60s
```

## 🔍 Debugging Tests

### Test Debugging

```python
# Enable debug logging in tests
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pytest-sugar for better output
pytest --tb=short -v

# Use pytest-xdist for parallel execution
pytest -n auto

# Use pytest-watch for automatic re-running
ptw -- tests/
```

### Performance Profiling

```python
# Memory profiling
import tracemalloc

tracemalloc.start()
# ... your code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()

# CPU profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... your code ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 📈 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install poetry
        poetry install

    - name: Run tests
      run: |
        poetry run pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## 📊 Test Metrics

### Coverage Targets

- **Overall Coverage**: 95%+
- **Critical Paths**: 100%
- **Agent Logic**: 95%+
- **API Endpoints**: 100%
- **Database Operations**: 90%+

### Performance Targets

- **Response Time**: < 2s for 95% of requests
- **Memory Usage**: < 2GB under normal load
- **Concurrent Users**: Support 100+ users
- **Error Rate**: < 1% under normal load

## 🚨 Troubleshooting

### Common Test Issues

1. **Async Test Failures**
   ```python
   # Make sure to use @pytest.mark.asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

2. **Database Connection Issues**
   ```python
   # Use proper cleanup in fixtures
   @pytest.fixture
   async def test_db():
       engine = create_async_engine("sqlite+aiosqlite:///:memory:")
       yield engine
       await engine.dispose()  # Important!
   ```

3. **Mock Configuration**
   ```python
   # Ensure mocks are properly configured
   @patch("module.function", new_callable=AsyncMock)
   def test_with_mock(mock_function):
       mock_function.return_value = expected_value
       # Test implementation...
   ```

---

**📚 Więcej informacji**: Zobacz [Dokumentację Architektury](ARCHITECTURE_DOCUMENTATION.md) dla szczegółów implementacji.
