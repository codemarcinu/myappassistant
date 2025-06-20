"""
Middleware dla obsługi błędów i logowania
"""

import logging
import time
import uuid
from typing import Any, Callable, Dict

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .exceptions import (
    BaseCustomException,
    convert_system_exception,
    log_exception_with_context,
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and logging"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = None
        try:
            response = await call_next(request)
            return response

        except HTTPException as http_exc:
            # Already formatted HTTP exceptions
            return http_exc

        except BaseCustomException as custom_exc:
            # Convert custom exceptions to HTTP responses
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": getattr(custom_exc, "message", str(custom_exc)),
                        "details": getattr(custom_exc, "details", None),
                    }
                },
            )

        except Exception as exc:
            # Convert all other exceptions
            custom_exc = convert_system_exception(exc)
            self.logger.error(
                f"Unhandled exception in {request.url.path}",
                exc_info=True,
                extra={
                    "request": {
                        "method": request.method,
                        "path": request.url.path,
                        "headers": dict(request.headers),
                    }
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": getattr(custom_exc, "message", str(custom_exc)),
                        "details": getattr(custom_exc, "details", None),
                    }
                },
            )

        finally:
            # Log request metrics
            duration = time.time() - start_time
            status_code = getattr(response, "status_code", 500) if response else 500
            self.logger.info(
                f"Request {request.method} {request.url.path}",
                extra={"duration": duration, "status": status_code},
            )


def setup_error_middleware(app: ASGIApp) -> None:
    """Add error handling middleware to FastAPI app"""
    app.add_middleware(ErrorHandlingMiddleware)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware do szczegółowego logowania żądań"""

    def __init__(self, app, log_body: bool = False, log_headers: bool = True):
        super().__init__(app)
        self.log_body = log_body
        self.log_headers = log_headers

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Loguje szczegóły żądania i odpowiedzi"""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Log request details
        await self._log_request_details(request, request_id)

        # Process request
        response = await call_next(request)

        # Log response details
        await self._log_response_details(request, response, request_id, start_time)

        return response

    async def _log_request_details(self, request: Request, request_id: str):
        """Loguje szczegóły żądania"""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path_params": request.path_params,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        if self.log_headers:
            log_data["headers"] = dict(request.headers)

        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    log_data["body"] = body.decode("utf-8")
            except Exception:
                log_data["body"] = "Unable to read body"

        logger.debug(f"Request details: {log_data}")

    async def _log_response_details(
        self, request: Request, response: Response, request_id: str, start_time: float
    ):
        """Loguje szczegóły odpowiedzi"""
        processing_time = time.time() - start_time

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time": processing_time,
            "response_headers": dict(response.headers),
        }

        logger.debug(f"Response details: {log_data}")


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware do monitorowania wydajności"""

    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitoruje wydajność żądania"""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Log slow requests
        if processing_time > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url} "
                f"took {processing_time:.2f}s (threshold: {self.slow_request_threshold}s)"
            )

        # Add processing time to response headers
        response.headers["X-Processing-Time"] = str(processing_time)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware dodający nagłówki bezpieczeństwa"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dodaje nagłówki bezpieczeństwa do odpowiedzi"""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Middleware do obsługi CORS"""

    def __init__(self, app, allowed_origins: list = None, allowed_methods: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Obsługuje CORS"""
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            if origin in self.allowed_origins or "*" in self.allowed_origins:
                return JSONResponse(
                    status_code=200,
                    content={},
                    headers={
                        "Access-Control-Allow-Origin": origin or "*",
                        "Access-Control-Allow-Methods": ", ".join(self.allowed_methods),
                        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "86400",  # 24 hours
                    },
                )

        # Process normal requests
        response = await call_next(request)

        # Add CORS headers to all responses
        origin = request.headers.get("origin")
        if origin in self.allowed_origins or "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"

        response.headers["Access-Control-Allow-Methods"] = ", ".join(
            self.allowed_methods
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response
