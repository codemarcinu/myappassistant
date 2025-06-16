# My AI Assistant - Modular Agent System

## Overview

My AI Assistant is a modular, agent-based AI system designed to provide a conversational interface for various household tasks. It combines multiple specialized agents to manage shopping, assist with cooking, provide weather updates, and perform web searches. The system leverages locally-hosted language models via Ollama to ensure user privacy and data control.

## Key Features

- **Multi-Agent Architecture**: A robust system of specialized agents for different domains:
  - **Chef Agent**: Suggests recipes based on available pantry items.
  - **Weather Agent**: Provides real-time weather forecasts.
  - **Search Agent**: Fetches information from the web.
  - **OCR Agent**: Extracts data from receipt images.
- **Next.js Frontend**: A modern, interactive user interface built with Next.js and TypeScript.
- **Natural Language Understanding**: Capable of processing complex, multi-threaded commands.
- **Local LLM Integration**: Utilizes Ollama for running language models locally, ensuring privacy.
- **Database Storage**: Tracks pantry items, receipts, and user preferences using a local database.
- **Receipt Scanning**: Automates receipt entry through advanced OCR technology.

## System Architecture

The project is a monorepo containing two main components: a FastAPI backend and a Next.js frontend.

### Backend (`src/backend/`)

The backend is built with Python and FastAPI, handling the core logic and agent orchestration.

- **Agents (`src/backend/agents/`)**: The intelligence layer of the system.
  - `orchestrator.py`: The central controller that routes requests to the appropriate specialized agent.
  - `agent_factory.py`: A factory for creating agent instances.
  - `base_agent.py`: The base class for all agents.
  - `*_agent.py`: Specialized agents for cooking, weather, search, and OCR.
- **API (`src/backend/api/`)**: FastAPI endpoints for communication with the frontend.
- **Core (`src/backend/core/`)**: Fundamental services like database management, LLM client, and OCR processing.

### Frontend (`foodsave-frontend/`)

The frontend is a modern web application built with Next.js and TypeScript.

- **App Router (`foodsave-frontend/src/app/`)**: Manages application routing and pages.
- **Components (`foodsave-frontend/src/components/`)**: Reusable React components, organized by feature.
- **Services (`foodsave-frontend/src/services/`)**: Handles business logic and API communication.
- **Hooks (`foodsave-frontend/src/hooks/`)**: Custom React hooks for state management and side effects.

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **AI**: Ollama, LangChain
- **Database**: SQLite (default), compatible with PostgreSQL
- **DevOps**: Docker, Poetry

## Setup & Installation

### Prerequisites

- Python 3.9+ (3.11+ recommended)
- Node.js 18.x or higher
- [Ollama](https://ollama.com/) for local language models
- [Poetry](https://python-poetry.org/) for Python dependency management

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Set up the Backend:**
    ```bash
    # Install Python dependencies
    poetry install

    # Activate the virtual environment
    poetry shell
    ```

3.  **Set up the Frontend:**
    ```bash
    # Navigate to the frontend directory
    cd foodsave-frontend

    # Install Node.js dependencies
    npm install
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the project root by copying `.env.example` and customize the variables.
    ```bash
    cp .env.example .env
    ```

5.  **Set up Ollama:**
    Install Ollama from the [official website](https://ollama.com/) and pull the required models:
    ```bash
    ollama pull gemma3:12b
    ollama pull deepseek-coder-v2:16b
    ollama pull nomic-embed-text
    ```

6.  **Initialize the Database:**
    ```bash
    # Make sure you are in the root directory with the Poetry shell activated
    python scripts/seed_db.py
    ```

### Running the Application

1.  **Start the Backend Server:**
    ```bash
    # From the project root, with Poetry shell activated
    uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

2.  **Start the Frontend Development Server:**
    In a new terminal, navigate to the frontend directory:
    ```bash
    cd foodsave-frontend
    npm run dev
    ```

The application will be available at `http://localhost:3000`.

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

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
