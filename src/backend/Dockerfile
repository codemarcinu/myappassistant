FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install from requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Make sure the directory is treated as a Python package
RUN touch __init__.py

# Set Python path to include the parent directory
ENV PYTHONPATH=/

# Run with the Python module notation to handle imports correctly
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
