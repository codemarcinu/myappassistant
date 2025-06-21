#!/usr/bin/env python3
"""
Prosty test backend do sprawdzenia logowania
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

# Tworzenie katalogów logów
logs_dir = Path("logs/backend")
logs_dir.mkdir(parents=True, exist_ok=True)

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # stdout
        logging.FileHandler(os.path.join(logs_dir, "app.log"), encoding="utf-8"),
        logging.FileHandler(os.path.join(logs_dir, "error.log"), encoding="utf-8"),
    ],
)

# Dodanie filtra dla error.log
error_handler = logging.FileHandler(
    os.path.join(logs_dir, "error.log"), encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)
logging.getLogger().addHandler(error_handler)

logger = logging.getLogger(__name__)

app = FastAPI(title="Test Backend", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    logger.info("Test backend starting up...")
    logger.info(f"Logs directory: {logs_dir}")


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Test Backend is running!"}


@app.get("/health")
async def health():
    logger.info("Health check requested")
    return {"status": "healthy", "service": "test-backend"}


@app.get("/test-log")
async def test_log():
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    return {"message": "Log messages written"}


@app.get("/logs")
async def get_logs():
    """Endpoint do pobierania logów"""
    try:
        log_file = os.path.join(logs_dir, "app.log")
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            return {"logs": content}
        else:
            return {"logs": "Log file not found"}
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs/stream")
async def stream_logs():
    """Endpoint do streamowania logów w czasie rzeczywistym"""

    async def log_generator():
        log_file = os.path.join(logs_dir, "app.log")
        if not os.path.exists(log_file):
            yield f"data: {json.dumps({'error': 'Log file not found'})}\n\n"
            return

        # Wysyłanie istniejących logów
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                yield f"data: {json.dumps({'log': line.strip()})}\n\n"

        # Monitorowanie nowych logów (uproszczone)
        yield f"data: {json.dumps({'status': 'streaming_complete'})}\n\n"

    return StreamingResponse(
        log_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    logger.info("Starting test backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
