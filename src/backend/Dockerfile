FROM python:3.12-slim

# Install system dependencies including tesseract-ocr and build essentials
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    build-essential \
    swig \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install poetry with increased network timeout
RUN pip install poetry --timeout 300 && \
    poetry config virtualenvs.create false && \
    pip config set global.timeout 600

# Copy dependency files
COPY pyproject.toml poetry.lock /app/

# Install core dependencies first
RUN pip install --retries 3 --timeout 300 fastapi uvicorn python-multipart httpx pydantic pydantic-settings python-dotenv \
    sqlalchemy aiosqlite pytz psutil

# Install ML dependencies in smaller groups with alternatives to problematic packages
RUN pip install --retries 5 --timeout 600 \
    langchain==0.1.0 \
    langchain-community==0.0.13 \
    numpy==1.26.0 \
    scipy==1.15.3 \
    scikit-learn==1.7.0 \
    pytesseract==0.3.10 \
    PyMuPDF==1.24.1 \
    ollama==0.1.0

# Install sentence-transformers (which includes a GPU-enabled pytorch)
RUN pip install --retries 5 --timeout 600 sentence-transformers==2.2.2

# Copy backend code
COPY . /app/backend

# Set environment variables
ENV PYTHONPATH=/app

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
