from __future__ import annotations
from backend.app_factory import create_app
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

app = create_app()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Set error_code based on status_code
    if exc.status_code >= 500:
        error_code = "INTERNAL_SERVER_ERROR"
    elif exc.status_code >= 400:
        error_code = "CLIENT_ERROR"
    else:
        error_code = "HTTP_ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": error_code,
            "path": str(request.url.path)
        }
    )
