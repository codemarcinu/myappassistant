# FoodSave AI - Enhanced Modular Agent System

## 🚀 Quick Start

**Najszybszy sposób uruchomienia aplikacji:**

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/yourusername/foodsave-ai.git
cd foodsave-ai

# 2. Uruchom aplikację jednym poleceniem
./run_all.sh
```

**Aplikacja będzie dostępna pod adresami:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Dokumentacja API: http://localhost:8000/docs

**Aby zatrzymać aplikację:**
```bash
./stop_all.sh
```

---

## Overview

FoodSave AI is a sophisticated, agent-based AI system designed to provide a conversational interface for various household tasks with a focus on food management and sustainability. It features an enhanced agent architecture with improved RAG capabilities, memory management, and specialized agents to manage shopping, assist with cooking, provide weather updates, and perform web searches. The system leverages locally-hosted language models via Ollama to ensure user privacy and data control.

## Key Features

- **Enhanced Multi-Agent Architecture**: A robust system of specialized agents with improved capabilities:
  - **Chef Agent**: Suggests recipes based on available pantry items.
  - **Enhanced Weather Agent**: Provides real-time weather forecasts with improved context awareness.
  - **Search Agent**: Fetches information from the web with improved relevance filtering.
  - **OCR Agent**: Extracts data from receipt images.
  - **Analytics Agent**: Provides insights into shopping patterns.
  - **Meal Planner Agent**: Helps with planning meals and generating shopping lists.
  - **Categorization Agent**: Automatically categorizes products from receipts.
  - **Enhanced RAG Agent**: Performs advanced Retrieval-Augmented Generation for superior conversational capabilities.
- **Next.js Frontend**: A modern, interactive user interface built with Next.js and TypeScript.
- **Advanced Natural Language Understanding**: Capable of processing complex, multi-threaded commands with improved context retention.
- **Local LLM Integration**: Utilizes Ollama for running language models locally, ensuring privacy.
- **Enhanced Memory Management**: Improved conversation state tracking and user preference management.
- **Database Storage**: Tracks pantry items, receipts, and user preferences using a local database.
- **Receipt Scanning**: Automates receipt entry through advanced OCR technology.

## System Architecture

The project is a monorepo containing two main components: a FastAPI backend and a Next.js frontend.

### Backend (`src/backend/`)

The backend is built with Python and FastAPI, handling the core logic and agent orchestration.

- **Agents (`src/backend/agents/`)**: The intelligence layer of the system.
  - `enhanced_orchestrator.py`: The central controller that intelligently routes requests to specialized agents.
  - `agent_factory.py`: A factory for creating agent instances.
  - `enhanced_base_agent.py`: The improved base class for all agents with enhanced error handling.
  - Specialized enhanced agents for cooking, weather, search, and information retrieval.
- **API (`src/backend/api/`)**: FastAPI endpoints for communication with the frontend.
- **Core (`src/backend/core/`)**: Enhanced services including:
  - `enhanced_vector_store.py`: Improved vector storage for RAG capabilities.
  - `hybrid_llm_client.py`: Flexible LLM integration supporting multiple models.
  - `memory.py`: Advanced conversation memory management.
  - `rag_document_processor.py`: Optimized document processing for RAG.

### Frontend (`foodsave-frontend/`)

The frontend is a modern web application built with Next.js and TypeScript.

- **App Router (`foodsave-frontend/src/app/`)**: Manages application routing and pages.
- **Components (`foodsave-frontend/src/components/`)**: Reusable React components, organized by feature.
- **Services (`foodsave-frontend/src/services/`)**: Handles business logic and API communication.
- **Hooks (`foodsave-frontend/src/hooks/`)**: Custom React hooks for state management and side effects.

## Enhanced Architecture Diagram

```mermaid
graph TD
    User[User] --> Frontend[Next.js Frontend]
    Frontend --> API[FastAPI Backend]
    API --> EO[Enhanced Orchestrator]

    EO --> Memory[Memory Manager]
    EO --> Intent[Intent Recognition]

    EO --> ERAG[Enhanced RAG Agent]
    EO --> EWA[Enhanced Weather Agent]
    EO --> Search[Search Agent]
    EO --> Chef[Chef Agent]
    EO --> Other[Other Specialized Agents]

    ERAG --> EVS[Enhanced Vector Store]
    ERAG --> HLLM[Hybrid LLM Client]

    subgraph "Knowledge Base"
        EVS --> FAISS[FAISS Index]
        EVS --> Documents[Document Storage]
    end

    subgraph "External Services"
        EWA --> Weather[Weather APIs]
        Search --> WebSearch[Web Search]
    end
```

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **AI**: Ollama, LangChain, FAISS, Sentence Transformers
- **Database**: SQLite (default), compatible with PostgreSQL
- **DevOps**: Docker, Poetry
- **Testing**: pytest, pytest-cov, pytest-asyncio, Locust
- **Code Quality**: black, isort, flake8, ruff, mypy

## Setup & Installation

### Prerequisites

- **Python 3.12+**
- **Node.js 18.x or higher**
- **[Ollama](https://ollama.com/)** for local language models
- **[Poetry](https://python-poetry.org/)** for Python dependency management

### Automatic Setup (Recommended)

The easiest way to get started is using the provided script:

```bash
# Clone the repository
git clone https://github.com/yourusername/foodsave-ai.git
cd foodsave-ai

# Run the setup script (this will install everything and start the app)
./run_all.sh
```

The script will:
- ✅ Check all prerequisites
- ✅ Install Python dependencies
- ✅ Install Node.js dependencies
- ✅ Set up environment variables
- ✅ Start the backend and frontend
- ✅ Verify everything is working

### Manual Setup

If you prefer to set up manually:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/foodsave-ai.git
    cd foodsave-ai
    ```

2. **Set up the Backend:**
    ```bash
    # Install Python dependencies
    poetry install

    # Activate the virtual environment
    poetry shell
    ```

3. **Set up the Frontend:**
    ```bash
    # Navigate to the frontend directory
    cd foodsave-frontend

    # Install Node.js dependencies
    npm install
    ```

4. **Configure Environment Variables:**
    The `run_all.sh` script will create a `.env` file automatically, or you can create it manually:
    ```bash
    cp .env.example .env
    ```

    Required API keys (optional - app will work without them):
    - **NEWS_API_KEY**: Register at [newsapi.org](https://newsapi.org/register)
    - **BING_SEARCH_API_KEY**: Create a Bing Search API resource in [Azure Cognitive Services](https://portal.azure.com/#create/Microsoft.CognitiveServicesBingSearch-v7)

5. **Set up Ollama:**
    ```bash
    # Install Ollama
    curl -fsSL https://ollama.com/install.sh | sh

    # Pull required models (minimum 16GB RAM recommended)
    ollama pull gemma3:latest  # ~5GB
    ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q6_K  # ~7GB
    ollama pull nomic-embed-text  # ~0.5GB

    # Start Ollama
    ollama serve
    ```

6. **Start the Application:**
    ```bash
    # Start backend
    cd src/backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

    # In another terminal, start frontend
    cd foodsave-frontend
    npm run dev
    ```

### Docker Setup

For containerized deployment:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use the rebuild script
./rebuild.sh
```

## Usage

### Starting the Application

```bash
# Quick start (recommended)
./run_all.sh

# Manual start
./stop_all.sh  # Stop any running instances first
./run_all.sh   # Start fresh
```

### Stopping the Application

```bash
./stop_all.sh
```

### Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Troubleshooting

**Common Issues:**

1. **Port already in use:**
   ```bash
   ./stop_all.sh  # Stop existing processes
   ./run_all.sh   # Start fresh
   ```

2. **Ollama not running:**
   ```bash
   ollama serve
   ```

3. **Dependencies not installed:**
   ```bash
   poetry install
   cd foodsave-frontend && npm install
   ```

4. **Permission denied:**
   ```bash
   chmod +x run_all.sh stop_all.sh
   ```

**Logs:**
- Backend logs: `backend.log`
- Frontend logs: `frontend.log`
- Ollama logs: `journalctl -u ollama -f` (Linux)

## Testing Approach

The project uses a comprehensive testing strategy:

### Test Types
- **Unit Tests**: Test individual components in isolation (`tests/unit/`)
- **Integration Tests**: Test API endpoints and component interactions (`tests/integration/`)
- **E2E Tests**: Test complete workflows (`tests/e2e/`)
- **Performance Tests**: Load testing with Locust (`locustfile.py`)

### Running Tests
```bash
# Run all tests with coverage
pytest --cov=src tests/ -v

# Run specific test type
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run performance tests
locust -f locustfile.py
```

### Test Coverage
- Current coverage: ~85% (target: 90%)
- Generate coverage report:
  ```bash
  pytest --cov=src --cov-report=html tests/
  ```

### Mockowanie LLM w testach agentów

Aby testować agentów korzystających z LLM (np. llm_client.chat lub hybrid_llm_client.chat), użyj poniższego wzorca, który obsługuje zarówno tryb stream (stream=True), jak i zwykły (stream=False):

```python
def make_llm_chat_mock(stream_content: str, non_stream_content: str = None):
    """
    Zwraca funkcję do mockowania llm_client.chat/hybrid_llm_client.chat,
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
```

**Przykład użycia w teście:**

```python
@patch("backend.agents.weather_agent.llm_client", new_callable=AsyncMock)
def test_weather_agent(mock_llm_client):
    mock_llm_client.chat = make_llm_chat_mock(
        stream_content="Słonecznie, 25 stopni.",
        non_stream_content="Słonecznie, 25 stopni."
    )
    # ...reszta testu...
```

Możesz użyć tego wzorca dla wszystkich agentów korzystających z LLM, zarówno dla streamowania, jak i odpowiedzi jednorazowych.

## Model Requirements

Different models have varying hardware requirements:

| Model Name            | RAM Required | VRAM Required | Disk Space |
|-----------------------|--------------|---------------|------------|
| gemma3:latest         | 8GB          | 4GB           | 5GB        |
| SpeakLeash/bielik-11b | 16GB         | 8GB           | 7GB        |
| nomic-embed-text      | 4GB          | 2GB           | 0.5GB      |

### Performance Optimization

1. **GPU Acceleration**:
   - Install NVIDIA drivers and CUDA toolkit
   - Set `OLLAMA_GPU=1` environment variable
   - Use `--gpu` flag with Ollama

2. **Memory Optimization**:
   - Use smaller models for limited RAM
   - Reduce context window size
   - Enable swap space if needed

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the logs in `backend.log` and `frontend.log`

# FoodSave AI Backend

Inteligentny system asystenta kulinarnego z wieloma agentami AI, optymalizacją pamięci i monitoringiem w czasie rzeczywistym.

## Architektura Systemu

### Diagram Architektury

```mermaid
flowchart TD
    subgraph API_Layer
        A1[FastAPI Endpoints]
        A2[MemoryMonitoringMiddleware]
        A3[PerformanceMonitoringMiddleware]
        A4[ErrorHandlingMiddleware]
    end
    subgraph Orchestration
        B1[Orchestrator Pool]
        B2[Request Queue]
        B3[CircuitBreakerMonitor]
    end
    subgraph Agents
        C1[ChefAgent]
        C2[SearchAgent]
        C3[MealPlannerAgent]
        C4[OCRAgent]
        C5[RAGAgent]
        C6[WeatherAgent]
    end
    subgraph Core_Services
        D1[MemoryManager]
        D2[VectorStore]
        D3[RAGDocumentProcessor]
        D4[CacheManager]
        D5[HybridLLMClient]
        D6[ProfileManager]
    end
    subgraph Infrastructure
        E1[Database_SQLAlchemy_Async]
        E2[Redis_Cache]
        E3[FAISS_Index]
        E4[Prometheus_Metrics]
        E5[OpenTelemetry_Tracing]
    end
    subgraph Monitoring_Alerting
        F1[Prometheus_Metrics_Endpoint]
        F2[AlertManager]
        F3[Health_Checks]
    end

    A1 -->|Request| A2 --> A3 --> A4 --> B1
    B1 -->|Dispatch| B2
    B1 -->|Route| C1
    B1 -->|Route| C2
    B1 -->|Route| C3
    B1 -->|Route| C4
    B1 -->|Route| C5
    B1 -->|Route| C6
    C1 --> D1
    C2 --> D2
    C3 --> D1
    C4 --> D3
    C5 --> D2
    C6 --> D1
    D1 --> E1
    D2 --> E3
    D3 --> E1
    D4 --> E2
    D5 --> E1
    D6 --> E1
    A1 --> F1
    D1 --> F1
    D2 --> F1
    D3 --> F1
    D4 --> F1
    D5 --> F1
    D6 --> F1
    F1 -->|Metrics| E4
    A1 --> F2
    F2 -->|Alert| A1
    F2 -->|Alert| F3
    F3 -->|Status| A1
    E5 -.-> A1
    E5 -.-> D1
    E5 -.-> D2
    E5 -.-> D3
    E5 -.-> D4
    E5 -.-> D5
    E5 -.-> D6
    E5 -.-> B1
    E5 -.-> C1
    E5 -.-> C2
    E5 -.-> C3
    E5 -.-> C4
    E5 -.-> C5
    E5 -.-> C6
    E4 -.-> Prometheus[Prometheus_Server]
    E5 -.-> Jaeger[Jaeger_Tracing_Backend]
```

### Opis Komponentów

#### API Layer
- **FastAPI Endpoints**: RESTful API z automatyczną dokumentacją
- **MemoryMonitoringMiddleware**: Monitorowanie użycia pamięci w czasie rzeczywistym
- **PerformanceMonitoringMiddleware**: Śledzenie wydajności endpointów
- **ErrorHandlingMiddleware**: Centralne zarządzanie błędami i logowanie

#### Orchestration
- **Orchestrator Pool**: Pula orkiestratorów do zarządzania agentami
- **Request Queue**: Kolejka żądań z obsługą backpressure
- **CircuitBreakerMonitor**: Monitorowanie stanu circuit breakers

#### Agents
- **ChefAgent**: Agent kulinarny do planowania posiłków
- **SearchAgent**: Agent wyszukiwania przepisów
- **MealPlannerAgent**: Agent planowania posiłków
- **OCRAgent**: Agent OCR do przetwarzania paragonów
- **RAGAgent**: Agent RAG do wyszukiwania dokumentów
- **WeatherAgent**: Agent pogodowy

#### Core Services
- **MemoryManager**: Zarządzanie pamięcią z weak references
- **VectorStore**: FAISS-based vector store z memory mapping
- **RAGDocumentProcessor**: Przetwarzanie dokumentów RAG
- **CacheManager**: Redis cache manager
- **HybridLLMClient**: Klient LLM z fallback strategies
- **ProfileManager**: Zarządzanie profilami użytkowników

#### Infrastructure
- **Database**: SQLAlchemy Async z connection pooling
- **Redis Cache**: Cache z TTL i eviction policies
- **FAISS Index**: Vector index z memory optimization
- **Prometheus Metrics**: Metryki systemowe i aplikacyjne
- **OpenTelemetry Tracing**: Distributed tracing

#### Monitoring & Alerting
- **Prometheus Metrics Endpoint**: `/metrics` endpoint
- **AlertManager**: System alertów z regułami
- **Health Checks**: Endpointy `/health`, `/ready`, `/api/v1/status`

## Performance i Optymalizacje

### Zoptymalizowane Komponenty

1. **Memory Management**
   - Weak references dla unikania memory leaks
   - Context managers dla proper resource cleanup
   - `__slots__` dla klas z dużą liczbą instancji
   - Memory profiling z tracemalloc

2. **Async Patterns**
   - FastAPI z async/await
   - SQLAlchemy Async z connection pooling
   - asyncio.gather() dla parallel operations
   - Backpressure mechanizmy

3. **Database Optimization**
   - Connection pooling (pool_size=20, max_overflow=10)
   - Lazy loading dla relationships
   - Query batching dla bulk operations
   - Pagination dla large result sets

4. **Vector Store Optimization**
   - FAISS IndexIVFFlat z Product Quantization
   - Memory mapping dla vector files
   - LRU cache dla embeddings
   - Batch processing dla vector operations

5. **Monitoring & Observability**
   - Prometheus metrics dla wszystkich komponentów
   - OpenTelemetry distributed tracing
   - Custom alerting system
   - Health checks dla wszystkich services

### Benchmarki Wydajności

```
test_snapshot_creation_benchmark:     561.9950 ns (Min) - 47,179,392.9974 ns (Max)
test_async_snapshot_benchmark:        1,151.9951 ns (Min) - 59,956.0008 ns (Max)
test_performance_metrics_benchmark:   227,381.0023 ns (Min) - 365,519.0012 ns (Max)
```

### Endpointy Monitoringu

- `/metrics` - Prometheus metrics
- `/api/v1/metrics` - JSON metrics
- `/api/v1/status` - Detailed system status
- `/api/v1/alerts` - Active alerts
- `/api/v1/alerts/history` - Alert history
- `/health` - Basic health check
- `/ready` - Readiness check

## Instalacja i Uruchomienie

### Wymagania
- Python 3.12+
- Redis
- SQLite (lub PostgreSQL)
- Tesseract OCR

### Instalacja
```bash
# Klonowanie repozytorium
git clone <repository-url>
cd my_ai_assistant

# Instalacja zależności
poetry install

# Konfiguracja środowiska
cp .env.example .env
# Edytuj .env z odpowiednimi wartościami

# Uruchomienie
poetry run python src/backend/main.py
```

### Docker
```bash
# Uruchomienie z Docker Compose
docker-compose up -d

# Uruchomienie w trybie development
docker-compose -f docker-compose.dev.yaml up -d
```

## Testy

### Uruchomienie testów
```bash
# Wszystkie testy
poetry run pytest

# Testy wydajnościowe
poetry run pytest src/backend/tests/performance/ --benchmark-only

# Testy z coverage
poetry run pytest --cov=backend --cov-report=html
```

### Struktura testów
- `tests/unit/` - Testy jednostkowe
- `tests/integration/` - Testy integracyjne
- `tests/performance/` - Testy wydajnościowe
- `tests/e2e/` - Testy end-to-end

## Dokumentacja API

Dokumentacja API jest dostępna pod adresem `/docs` (Swagger UI) po uruchomieniu aplikacji.

## Monitoring i Alerty

### Prometheus
Metryki są eksportowane na endpoint `/metrics` w formacie Prometheus.

### Alerty
System alertów monitoruje:
- Użycie pamięci > 80%
- Użycie CPU > 90%
- Błędy bazy danych > 5
- Error rate > 10%
- Response time > 2s

### Health Checks
- `/health` - Podstawowy health check
- `/ready` - Sprawdzenie gotowości wszystkich komponentów
- `/api/v1/status` - Szczegółowy status systemu

## Rozwój

### Struktura projektu
```
src/backend/
├── agents/           # Agenty AI
├── api/             # Endpointy API
├── core/            # Core services
├── infrastructure/  # Infrastructure layer
├── models/          # Database models
├── tests/           # Testy
└── main.py          # Entry point
```

### Dodawanie nowego agenta
1. Utwórz nową klasę w `src/backend/agents/`
2. Zaimplementuj interfejs `IBaseAgent`
3. Dodaj do `AgentFactory`
4. Napisz testy jednostkowe
5. Dodaj do dokumentacji

### Dodawanie nowego endpointu
1. Utwórz router w `src/backend/api/`
2. Dodaj endpointy z proper error handling
3. Dodaj testy integracyjne
4. Zaktualizuj dokumentację API

## Licencja

MIT License - zobacz plik [LICENSE](LICENSE) dla szczegółów.
