# 🍽️ FoodSave AI - Intelligent Culinary Assistant

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)]()

> **Intelligent multi-agent AI system for sustainable food management and culinary assistance**

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📖 Project Overview](#-project-overview)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Technology Stack](#️-technology-stack)
- [📦 Installation & Setup](#-installation--setup)
- [🚀 Usage](#-usage)
- [🧪 Testing](#-testing)
- [📊 Monitoring](#-monitoring)
- [🔧 Troubleshooting](#-troubleshooting)
- [📚 Documentation](#-documentation)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## 🚀 Quick Start (Docker - Recommended)

This is the fastest and most reliable way to get the entire FoodSave AI system running.

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/foodsave-ai.git
cd foodsave-ai

# 2. Create environment file from the example
cp env.dev.example .env

# 3. Build and run all services in detached mode
docker compose up --build -d
```

**Application will be available at:**
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 📊 **Monitoring (Grafana)**: http://localhost:3001

**To stop the application:**
```bash
docker compose down
```

---

## 📖 Project Overview

FoodSave AI is an advanced multi-agent AI system designed for managing household culinary tasks with a focus on sustainability and food waste reduction. The system utilizes locally hosted language models through Ollama, ensuring privacy and user data control.

### 🎯 Key Features

- **🤖 Advanced Multi-Agent Architecture**: Specialized AI agents:
  - **👨‍🍳 Chef Agent**: Suggests recipes based on available ingredients
  - **🌤️ Weather Agent**: Provides real-time weather forecasts
  - **🔍 Search Agent**: Searches for information from the internet
  - **📷 OCR Agent**: Extracts data from receipt images
  - **📊 Analytics Agent**: Provides insights about shopping patterns
  - **📅 Meal Planner Agent**: Helps with meal planning
  - **🏷️ Categorization Agent**: Automatic product categorization
  - **🧠 RAG Agent**: Advanced Retrieval-Augmented Generation

- **⚡ Next.js Frontend**: Modern user interface with TypeScript
- **🧠 Advanced NLP**: Processing complex, multi-threaded commands
- **🔒 Local LLM Integration**: Uses Ollama for privacy
- **💾 Memory Management**: Enhanced conversation state tracking
- **🗄️ Database**: Tracks ingredients, receipts, and user preferences
- **📸 Receipt Scanning**: Automated receipt entry through OCR

## 🏗️ Architecture

### System Architecture Diagram

```mermaid
graph TD
    User[👤 User] --> Frontend[🌐 Next.js Frontend]
    Frontend --> API[🔧 FastAPI Backend]
    API --> EO[🎯 Enhanced Orchestrator]

    EO --> Memory[💾 Memory Manager]
    EO --> Intent[🧠 Intent Recognition]

    EO --> ERAG[🧠 Enhanced RAG Agent]
    EO --> EWA[🌤️ Enhanced Weather Agent]
    EO --> Search[🔍 Search Agent]
    EO --> Chef[👨‍🍳 Chef Agent]
    EO --> Other[🤖 Other Specialized Agents]

    ERAG --> EVS[📚 Enhanced Vector Store]
    ERAG --> HLLM[🤖 Hybrid LLM Client]

    subgraph "Knowledge Base"
        EVS --> FAISS[🔍 FAISS Index]
        EVS --> Documents[📄 Document Storage]
    end

    subgraph "External Services"
        EWA --> Weather[🌤️ Weather APIs]
        Search --> WebSearch[🌐 Web Search]
    end
```

### Project Structure

```
my_ai_assistant/
├── 📁 src/backend/           # Backend Python/FastAPI
│   ├── 🤖 agents/           # AI agents
│   ├── 🔧 api/              # API endpoints
│   ├── ⚙️ core/             # Core services
│   ├── 🗄️ infrastructure/   # Database, cache, etc.
│   ├── 📊 models/           # Database models
│   └── 🧪 tests/            # Backend tests
├── 🌐 foodsave-frontend/     # Frontend Next.js
│   ├── 📱 src/app/          # App router
│   ├── 🧩 src/components/   # React components
│   ├── 🔗 src/services/     # API services
│   └── 🧪 tests/            # Frontend tests
├── 📚 docs/                 # Documentation
├── 🐳 docker-compose.yaml   # Docker setup
└── 📋 README.md             # This file
```

## 🛠️ Technology Stack

### Backend
- **🐍 Python 3.12+** - Main programming language
- **⚡ FastAPI** - Modern API framework
- **🗄️ SQLAlchemy** - ORM with async support
- **🤖 Ollama** - Local language models
- **🔍 FAISS** - Vector search engine
- **📊 Prometheus** - Monitoring and metrics

### Frontend
- **⚛️ Next.js 14** - React framework
- **🔷 TypeScript** - Type safety
- **🎨 Tailwind CSS** - Styling
- **🔗 TanStack Query** - State management
- **🧪 Jest + Playwright** - Testing

### DevOps
- **🐳 Docker** - Containerization
- **📦 Poetry** - Python dependency management
- **🧪 Pytest** - Testing framework
- **📊 Grafana** - Monitoring dashboard

## 📦 Installation & Setup

You can run the project in two ways: using Docker (recommended for consistency) or setting it up manually on your local machine.

### Method 1: Docker Setup (Recommended)

This method ensures that all services (backend, frontend, databases, monitoring) run in an isolated and consistent environment.

#### Prerequisites
- **🐳 Docker** and **Docker Compose**
- **🌐 Git**

#### Steps
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/foodsave-ai.git
    cd foodsave-ai
    ```

2.  **Create Environment File:**
    Copy the development environment example file. No changes are needed to get started.
    ```bash
    cp env.dev.example .env
    ```

3.  **Build and Run:**
    This command will build the necessary Docker images and start all services.
    ```bash
    docker compose up --build -d
    ```
    > **Note on PostgreSQL Port:** If you have a local PostgreSQL instance running, you might encounter a port conflict on `5432`. The configuration uses port **5433** for the container to avoid conflicts.

4.  **Verify Services:**
    Check if all containers are running.
    ```bash
    docker ps
    ```
    You should see `foodsave-backend`, `foodsave-frontend`, `foodsave-ollama`, and others running.

### Method 2: Manual Local Setup

Use this method if you prefer to run the services directly on your machine without Docker.

#### Prerequisites
- **🐍 Python 3.12+**
- **📦 Poetry**
- **🟢 Node.js 20.x or higher**
- **🤖 [Ollama](https://ollama.com/)** installed and running.

#### Steps
1.  **Clone and Setup Environment:**
    ```bash
    git clone https://github.com/yourusername/foodsave-ai.git
    cd foodsave-ai
    cp env.dev.example .env
    ```

2.  **Backend Setup:**
    ```bash
    # Install Python dependencies
    poetry install
    # Activate virtual environment
    poetry shell
    # Run database migrations (if applicable)
    # poetry run alembic upgrade head
    ```

3.  **Frontend Setup:**
    ```bash
    # Navigate to frontend directory
    cd foodsave-frontend
    # Install Node.js dependencies
    npm install
    cd ..
    ```

4.  **Run the Application:**
    You can use the provided script to run all services locally.
    ```bash
    ./run_all.sh
    ```
    This script will start the backend, frontend, and check for Ollama.

## 🚀 Usage

### Starting the Application

- **Docker (Recommended):**
  ```bash
  docker compose up -d
  ```

- **Local Machine:**
  ```bash
  ./run_all.sh
  ```

### Accessing the Application

- **🌐 Frontend**: http://localhost:3000
- **🔧 Backend API**: http://localhost:8000
- **📚 API Docs**: http://localhost:8000/docs / http://localhost:8000/redoc
- **📊 Monitoring (Grafana)**: http://localhost:3001 (for Docker setup)

### Stopping the Application

- **Docker:**
  ```bash
  docker compose down
  ```

- **Local Machine:**
  ```bash
  ./stop_all.sh
  ```

## 🧪 Testing

### Running Backend Tests

```bash
# Install dependencies (if not done yet)
poetry install
# Run all tests
poetry run pytest tests/ -v
```

- To run a specific test type:
```bash
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
```

### Running Frontend Tests
```bash
cd foodsave-frontend
npm test
# For E2E tests
npm run test:e2e
```

### Test Coverage
- **Current coverage**: ~95% (target: 90%)
- **Generate coverage report**:
  ```bash
  poetry run pytest --cov=src --cov-report=html tests/
  ```

## 📊 Monitoring

The project is equipped with a monitoring stack available in the Docker setup.

### Monitoring Dashboards
- **Grafana**: http://localhost:3001 (user: `admin`, pass: `admin`)
  - Pre-configured dashboards for application and log metrics.
- **Prometheus**: http://localhost:9090
  - Scrapes metrics from the backend.

### Backend Health & Metric Endpoints
- **💚 Health Check**: `http://localhost:8000/health`
- **📊 Prometheus Metrics**: `http://localhost:8000/metrics`
- **✅ Readiness Check**: `http://localhost:8000/ready`
- **📋 System Status**: `http://localhost:8000/api/v1/status`

### System Metrics
- **Memory usage**: Real-time monitoring
- **API performance**: Response times, throughput
- **Agent status**: Health checks for all agents
- **Database**: Connection pool, query performance
- **Ollama logs**: Run `docker logs foodsave-ollama`
- **Combined logs**: Check Grafana's Loki data source.

## 🔧 Troubleshooting

### Common Issues

1. **Missing dependencies (ModuleNotFoundError, e.g. numpy):**
   ```bash
   poetry install
   ```
2. **Port already in use:**
   ```bash
   ./stop_all.sh  # Stop existing processes
   ./run_all.sh   # Start fresh
   ```
3. **Ollama not working:**
   ```bash
   ollama serve
   ```
4. **Permission error:**
   ```bash
   chmod +x run_all.sh stop_all.sh
   ```

### Logs
- **Backend logs**: `logs/backend/`
- **Frontend logs**: `logs/frontend/`
- **Ollama logs**: `journalctl -u ollama -f` (Linux)

## 📚 Documentation

### Quick Start
- **[📖 Documentation Hub](docs/README.md)** - Complete documentation overview
- **[🚀 Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[👨‍💻 Contributing Guide](docs/CONTRIBUTING_GUIDE.md)** - How to contribute to the project

### Technical Documentation

- **[🏗️ System Architecture](docs/ARCHITECTURE_DOCUMENTATION.md)** - Detailed architecture description
- **[🔧 API Reference](docs/API_REFERENCE.md)** - Complete API endpoints documentation
- **[🤖 AI Agents Guide](docs/AGENTS_GUIDE.md)** - AI agents and orchestration
- **[🗄️ Database Guide](docs/DATABASE_GUIDE.md)** - Database structure and management
- **[🧪 Testing Guide](docs/TESTING_GUIDE.md)** - Testing strategies and best practices
- **[🚀 Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[🔒 Security Guide](docs/SECURITY_GUIDE.md)** - Security and privacy (coming soon)

### Specialized Guides

- **[🤖 RAG System Guide](docs/RAG_SYSTEM_GUIDE.md)** - Retrieval-Augmented Generation
- **[📊 Model Optimization Guide](docs/MODEL_OPTIMIZATION_GUIDE.md)** - AI model optimization
- **[💾 Backup System Guide](docs/BACKUP_SYSTEM_GUIDE.md)** - Backup and recovery procedures

### Archived Documentation

- **[📋 MDC Setup Summary](docs/MDC_SETUP_SUMMARY.md)** - Model Development Cycle setup
- **[📝 Frontend Implementation Plan](docs/frontend-implementation-plan.md)** - Frontend development roadmap
- **[✅ Frontend Implementation Checklist](docs/frontend-implementation-checklist.md)** - Frontend development checklist

### Documentation by Role

**👨‍💻 Developers**: [Contributing Guide](docs/CONTRIBUTING_GUIDE.md) | [API Reference](docs/API_REFERENCE.md) | [Testing Guide](docs/TESTING_GUIDE.md)

**🚀 DevOps**: [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | [Backup System Guide](docs/BACKUP_SYSTEM_GUIDE.md) | [Model Optimization Guide](docs/MODEL_OPTIMIZATION_GUIDE.md)

**🤖 AI/ML Engineers**: [Agents Guide](docs/AGENTS_GUIDE.md) | [RAG System Guide](docs/RAG_SYSTEM_GUIDE.md) | [Model Optimization Guide](docs/MODEL_OPTIMIZATION_GUIDE.md)

**📊 Data Engineers**: [Database Guide](docs/DATABASE_GUIDE.md) | [Architecture Documentation](docs/ARCHITECTURE_DOCUMENTATION.md)

## 🤝 Contributing

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

### Coding Standards

- **Python**: Black, isort, flake8, mypy
- **TypeScript**: ESLint, Prettier
- **Tests**: Pytest for backend, Jest for frontend
- **Commit messages**: Conventional Commits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review logs in `logs/backend/` and `logs/frontend/`

## 📈 Project Status

- **🟢 Status**: Active Development
- **📅 Last Updated**: 2024-12-21
- **🐛 Issues**: [GitHub Issues](https://github.com/yourusername/foodsave-ai/issues)
- **📊 Coverage**: 95%+
- **🧪 Tests**: Passing

---

**🍽️ FoodSave AI** - Intelligent culinary assistant for sustainable living

## Rozwiązanie problemów z importami

W projekcie zidentyfikowano i rozwiązano problem niezgodności między strukturą importów w kodzie aplikacji a strukturą plików w kontenerze backend. Problem polegał na tym, że kod aplikacji używał importów zaczynających się od `src.backend`, podczas gdy w kontenerze pliki były umieszczone bezpośrednio w katalogu `/app`.

### Wdrożone rozwiązanie

Zastosowano podejście dostosowania struktury kontenerów do struktury kodu:

1. Zmodyfikowano plik `src/backend/Dockerfile.dev`, aby używał poprawnej ścieżki importu:
   ```python
   RUN echo 'from src.backend.app_factory import create_app\napp = create_app()' > main.py
   ```

2. Zaktualizowano plik `docker-compose.dev.yaml`, aby mapował cały katalog projektu:
   ```yaml
   volumes:
     - ./:/app  # Mapowanie całego katalogu projektu
   ```

3. Dostosowano komendę uruchamiającą aplikację:
   ```yaml
   command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level=debug"]
   ```

4. Dodano skrypt `fix_test_imports.py` do weryfikacji i naprawy importów w testach.

### Weryfikacja importów

Aby sprawdzić poprawność importów w projekcie, można użyć skryptu `fix_test_imports.py`:

```bash
python fix_test_imports.py
```

Skrypt analizuje strukturę importów i generuje raport kompatybilności, który pomaga zidentyfikować potencjalne problemy.

## 🧹 Project Cleanup 2024-06

**Status:** Project structure and codebase were thoroughly cleaned and refactored in June 2024. Key improvements:

- All temporary/debug/test log files removed from the root directory
- Python cache (`__pycache__`, `.pyc`, `.mypy_cache`) fully cleaned
- Database file `shopping.db` moved to `data/database/`
- All code-fix and repair scripts archived in `archive/code_fixes/`
- All critical imports refactored to use absolute import paths (see `.cursorrules`)
- Poetry is the recommended way to install dependencies and run tests
- Test configuration and coverage options updated for compatibility
- Project root is now clean and production-ready

**Best practices:**
- Keep root directory clean (no logs, temp files, or test artifacts)
- Always use absolute imports in backend Python code
- Archive or remove repair/utility scripts after use
- Use `poetry install` and `poetry run pytest` for backend development
- See `.cursorrules` for enforced code standards
