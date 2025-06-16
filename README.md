# My AI Assistant - Modular Agent System

## Overview

My AI Assistant is a modular agent-based AI system that combines multiple specialized agents to provide a conversational interface for various tasks including shopping management, cooking assistance, weather information, and web search. The system uses locally-hosted language models via Ollama for privacy and control.

## Key Features

- **Next.js Frontend**: Nowoczesny, interaktywny interfejs użytkownika zbudowany w oparciu o Next.js.
- **Multi-Agent Architecture**: Specialized agents for different domains:
  - **Chef Agent**: Suggests recipes based on available pantry items
  - **Weather Agent**: Provides weather forecasts for specified locations
  - **Search Agent**: Looks up information on the web
  - **OCR Agent**: Processes receipt images
- **Natural Language Understanding**: Processes complex, multi-threaded commands
- **Local LLM Integration**: Uses Ollama for running language models locally
- **Database Storage**: Tracks pantry items, receipts, and user preferences
- **Receipt Scanning**: OCR for automating receipt entry

## System Architecture

### Backend (`src/backend/`)
- **Agents**: The core intelligence layer
  - `orchestrator.py`: The main controller routing requests to specialized agents
  - `agent_factory.py`: Factory pattern for creating agent instances
  - `base_agent.py`: Base class for all agents
  - `*_agent.py`: Specialized agents (chef, weather, search, ocr)
  - `state.py`: Conversation state management
  - `tools/`: Tools for agent operations
- **API**: FastAPI-based endpoints
  - `agents.py`: Agent-related endpoints
  - `chat.py`: Chat conversation endpoints
  - `food.py`: Food and pantry endpoints
  - `receipts.py`: Receipt processing endpoints
- **Core**: Fundamental backend services
  - `database.py`: Database connection and models
  - `llm_client.py`: Client for Ollama LLM communication
  - `crud.py`: Data access layer
  - `ocr.py`: OCR processing for receipts

### Frontend (`foodsave-frontend/`)
- **Next.js Application**: Główna aplikacja frontendu.
- **Components**: Reużywalne komponenty UI.
- **Services**: Logika biznesowa i komunikacja z API.

## Setup & Installation

### Prerequisites
- Python 3.9+ (recommended: 3.11+)
- [Ollama](https://ollama.com/) for local language models
- Poetry for dependency management

### Installation

1. Clone the repository and install dependencies using Poetry:
```bash
# Install Poetry if needed
pip install poetry

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

2. Set up Ollama and pull the required models:
```bash
# Install Ollama following the instructions at https://ollama.com/
# Then pull the required models:
ollama pull gemma3:12b
ollama pull deepseek-coder-v2:16b
ollama pull nomic-embed-text
```

3. Create a `.env` file in the project root:
```
# Database
DATABASE_URL=sqlite+aiosqlite:///./shopping.db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_CHAT_MODEL=gemma3:12b
DEFAULT_CODE_MODEL=deepseek-coder-v2:16b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text:latest

# API
API_HOST=localhost
API_PORT=8000

# Frontend
```

4. Initialize the database:
```bash
python scripts/seed_db.py
```

### Running the Application

1. Start the backend server:
```bash
cd src/backend
uvicorn backend.main:app --reload
```

2. Start the frontend in a new terminal:
```bash
cd foodsave-frontend
npm run dev
```

The application will be available at http://localhost:3000

## API Endpoints

### Agent Endpoints
- `POST /api/v1/agents/execute`: Execute a task with the agent system

### Chat Endpoints
- `POST /api/v1/chat/`: Send a message to the chat system
- `GET /api/v1/chat/history`: Get chat history

### Pantry Endpoints
- `GET /api/v1/pantry/products`: Get all pantry products

### Receipt Endpoints
- `POST /api/v1/receipts/upload`: Upload and process a receipt image

## Example Usage

### Asking for Weather
```
User: "Jaka jest pogoda w Warszawie?"
Assistant: "Obecnie w Warszawie jest 22°C, częściowo zachmurzenie.
Wiatr wieje z prędkością 15 km/h, a wilgotność wynosi 65%."
```

### Getting a Recipe Suggestion
```
User: "Co mogę ugotować z produktów, które mam w spiżarni?"
Assistant: "Na podstawie produktów w Twojej spiżarni, proponuję:

PRZEPIS: Szybki makaron z sosem pomidorowym

Składniki:
- 200g makaronu penne
- 1 puszka pomidorów krojonych
- 2 ząbki czosnku
- 1 łyżka oliwy z oliwek
- Sól i pieprz do smaku
- Garść świeżej bazylii

Przygotowanie:
1. Ugotuj makaron al dente według instrukcji na opakowaniu.
2. Na patelni rozgrzej oliwę, dodaj posiekany czosnek i smaż przez 30 sekund.
3. Dodaj pomidory z puszki, sól i pieprz, gotuj na małym ogniu przez 10 minut.
4. Odcedź makaron i dodaj do sosu, wymieszaj.
5. Podawaj posypane świeżą bazylią.

Czy przygotowałeś to danie? To pozwoli mi zaktualizować stan spiżarni."
```

### OCR Receipt Processing
```
[User uploads a receipt image]
Assistant: "Pomyślnie przetworzono paragon! Rozpoznane produkty:
- Mleko 3,2% 1L: 3.99 zł
- Chleb pszenny: 4.50 zł
- Ser żółty 300g: 8.99 zł
- Pomidory 0.5kg: 4.29 zł

Łączna kwota: 21.77 zł. Czy chcesz, żebym dodał te produkty do Twojej spiżarni?"
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Development Mode
```bash
# Backend with hot reload
cd src/backend
uvicorn backend.main:app --reload --log-level debug

# Frontend with hot reload
cd foodsave-frontend
npm run dev
```

## Project Status

### Current Implementation
- ✅ Multi-agent orchestration system
- ✅ Next.js chat interface
- ✅ FastAPI backend with database integration
- ✅ Local LLM integration via Ollama
- ✅ Recipe suggestion based on pantry items
- ✅ Weather information retrieval
- ✅ OCR for receipt processing
- ✅ Basic conversation state management

### Upcoming Features
- ❌ Advanced analytics for shopping patterns
- ❌ Budget tracking and visualization
- ❌ Automated categorization of products
- ❌ Meal planning and shopping list generation
- ❌ User authentication system
- ❌ Mobile-friendly responsive design
- ❌ Improved conversation memory

## License

MIT License - see the LICENSE file for details.
