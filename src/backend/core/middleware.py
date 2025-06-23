"""
Middleware dla obsługi błędów i logowania
"""

import logging
import time
import uuid
from typing import Callable, Any, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.exceptions import BaseCustomException, convert_system_exception
from backend.core.monitoring import async_memory_profiling_context

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and logging"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = None
        try:
            response = await call_next(request)
            return response

        except HTTPException as http_exc:
            # Already formatted HTTP exceptions
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"detail": http_exc.detail},
                headers=http_exc.headers,
            )

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
            converted_exc = convert_system_exception(exc)
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
                        "message": getattr(converted_exc, "message", str(exc)),
                        "details": getattr(converted_exc, "details", None),
                    }
                },
            )


def setup_error_middleware(app: Any) -> None:
    """Add error handling middleware to FastAPI app"""
    app.add_middleware(ErrorHandlingMiddleware)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware do szczegółowego logowania żądań"""

    def __init__(self, app, log_body: bool = False, log_headers: bool = True) -> None:
        super().__init__(app)
        self.log_body = log_body
        self.log_headers = log_headers

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Loguje szczegóły żądania i odpowiedzi"""
        request_id = str(uuid.uuid4())

        # Log request details
        await self._log_request_details(request, request_id)

        # Process request
        response = await call_next(request)

        # Log response details
        await self._log_response_details(request, response, request_id)

        return response

    async def _log_request_details(self, request: Request, request_id: str) -> None:
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
        self, request: Request, response: Response, request_id: str
    ) -> None:
        """Loguje szczegóły odpowiedzi"""
        processing_time = time.time() - time.time()

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time": processing_time,
            "response_headers": dict(response.headers),
        }

        logger.debug(f"Response details: {log_data}")


class MemoryMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware do monitoringu pamięci dla FastAPI"""

    def __init__(self, app, enable_memory_profiling: bool = True) -> None:
        super().__init__(app)
        self.enable_memory_profiling = enable_memory_profiling

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch z memory monitoring"""
        if self.enable_memory_profiling:
            async with async_memory_profiling_context(
                f"request_{request.url.path}"
            ) as profiler:
                # Log start
                await profiler.log_memory_usage_async(
                    f"request_start_{request.url.path}"
                )

                # Process request
                response = await call_next(request)

                # Log end
                await profiler.log_memory_usage_async(f"request_end_{request.url.path}")

                # Add memory metrics to response headers
                metrics = await profiler.get_performance_metrics_async()
                response.headers["X-Memory-Usage-MB"] = str(
                    metrics.memory_rss / 1024 / 1024
                )
                response.headers["X-CPU-Percent"] = str(metrics.cpu_percent)

                return response
        else:
            # Simple timing without memory profiling
            response = await call_next(request)
            return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware do monitoringu wydajności"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch z performance monitoring"""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate timing
        process_time = time.time() - start_time

        # Add timing headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-Path"] = request.url.path

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

    def __init__(self, app, allowed_origins: Optional[list] = None, allowed_methods: Optional[list] = None) -> None:
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
