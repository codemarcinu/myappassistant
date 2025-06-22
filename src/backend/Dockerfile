FROM python:3.12-slim

# Install system dependencies including tesseract-ocr and build essentials
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    build-essential \
    swig \
    git \
    libopenblas-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
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
    sqlalchemy aiosqlite pytz psutil structlog==24.1.0 langdetect==1.0.9 redis==5.2.0 pybreaker==1.3.0 \
    dependency_injector>=4.41.0 slowapi==0.1.9 alembic asyncpg

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

# Install OpenTelemetry packages for monitoring and observability
RUN pip install --retries 3 --timeout 300 \
    opentelemetry-api==1.21.0 \
    opentelemetry-sdk==1.21.0 \
    opentelemetry-instrumentation-fastapi==0.42b0 \
    opentelemetry-instrumentation-sqlalchemy==0.42b0 \
    opentelemetry-instrumentation-httpx==0.42b0 \
    opentelemetry-exporter-jaeger==1.21.0 \
    prometheus-client==0.19.0 \
    prometheus-fastapi-instrumentator==6.1.0

# Install sentence-transformers (which includes a GPU-enabled pytorch)
RUN pip install --retries 5 --timeout 600 sentence-transformers==2.2.2

# Try to install faiss-cpu with multiple approaches
RUN pip install --no-cache-dir --retries 5 --timeout 600 faiss-cpu || \
    pip install --no-cache-dir --retries 5 --timeout 600 faiss-cpu==1.7.0 || \
    pip install --no-cache-dir --retries 5 --timeout 600 -i https://pypi.tuna.tsinghua.edu.cn/simple faiss-cpu || \
    echo "Warning: faiss-cpu installation failed, using scikit-learn as alternative"

# Copy backend code
COPY . /app/backend

# Set environment variables
ENV PYTHONPATH=/app

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
