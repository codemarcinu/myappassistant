import asyncio
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)

import structlog
from fastapi import APIRouter, BackgroundTasks, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.sql import text
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from backend.agents.orchestrator_factory import create_orchestrator
from backend.api import agents, chat, food, pantry, upload
from backend.api.v1.endpoints import receipts
from backend.api.v2.endpoints import rag as rag_v2
from backend.api.v2.endpoints import receipts as receipts_v2
from backend.api.v2.endpoints import weather as weather_v2
from backend.api.v2.exceptions import APIErrorDetail, APIException
from backend.config import settings
from backend.core.cache_manager import cache_manager
from backend.core.container import Container
from backend.core.database import AsyncSessionLocal
from backend.core.exceptions import (
    AIModelError,
    BaseCustomException,
    DatabaseError,
    FileProcessingError,
    NetworkError,
    ValidationError,
    convert_system_exception,
    log_exception_with_context,
)
from backend.core.middleware import CORSMiddleware as CustomCORSMiddleware
from backend.core.middleware import (
    ErrorHandlingMiddleware,
    PerformanceMonitoringMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from backend.core.migrations import run_migrations
from backend.core.monitoring import log_memory_usage
from backend.core.seed_data import seed_database
from backend.core.vector_store import vector_store
from backend.infrastructure.database.database import (
    AsyncSessionLocal,
    Base,
    check_database_health,
    engine,
)
from backend.orchestrator_management.orchestrator_pool import orchestrator_pool
from backend.orchestrator_management.request_queue import request_queue
from backend.core.alerting import AlertManager
from backend.core.cache_manager import CacheManager
from backend.core.database import init_db
from backend.core.hybrid_llm_client import HybridLLMClient
from backend.core.memory import MemoryManager
from backend.core.middleware import (
    MemoryMonitoringMiddleware,
    ResponseTimeMiddleware,
)
from backend.core.prometheus_metrics import metrics
from backend.core.telemetry import setup_telemetry
from backend.core.user_activity import UserActivityTracker

# Dodaj import klienta MMLW
try:
    from backend.core.mmlw_embedding_client import mmlw_client

    MMLW_AVAILABLE = True
except ImportError:
    MMLW_AVAILABLE = False

# Dodaj katalog projektu do PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Rate limiting ---
limiter = Limiter(key_func=get_remote_address)


# Configure structured logging
def configure_logging(log_level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=open("/dev/stdout", "w"),
        level=getattr(logging, log_level.upper()),
    )


# Initialize logging with default level
configure_logging(settings.LOG_LEVEL)
# Ensure debug level propagates to all loggers
logging.getLogger().setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

# Get logger after configuration
logger = structlog.get_logger()


# --- Middleware: Structured Logging ---
class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        # Add request-specific context
        structlog.contextvars.bind_contextvars(
            request_id=str(uuid.uuid4()),
            client_ip=request.client.host if request.client else "unknown",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
        )

        response = await call_next(request)

        # Log the request completion
        logger.info(
            "request.complete",
            status_code=response.status_code,
            response_size=len(response.body) if hasattr(response, "body") else 0,
        )

        return response


# --- Middleware: Auth (szkielet) ---
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Tu można dodać logikę JWT lub innej autoryzacji
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run migrations asynchronously
    await run_migrations()

    # Seed the database asynchronously
    logger.info("database.seeding.start")
    async with AsyncSessionLocal() as db:
        try:
            await seed_database(db)
        except Exception as e:
            logger.error("database.seeding.error", error=str(e))
            raise
    logger.info("database.seeding.complete")

    # Automatyczna inicjalizacja modelu MMLW jeśli włączony w configu
    if MMLW_AVAILABLE and settings.USE_MMLW_EMBEDDINGS:
        import asyncio

        try:
            logger.info("Auto-initializing MMLW embedding model...")
            success = await mmlw_client.initialize()
            if success:
                logger.info("MMLW model initialized successfully at startup.")
            else:
                logger.warning("MMLW model failed to initialize at startup.")
        except Exception as e:
            logger.error(f"Error initializing MMLW model at startup: {e}")

    # Initialize cache manager
    logger.info("Initializing cache manager...")
    cache_connected = await cache_manager.connect()
    if cache_connected:
        logger.info("Cache manager initialized successfully")
    else:
        logger.warning("Cache manager not available - continuing without cache")

    # Initialize orchestrator pool and request queue (using global instances)
    logger.info("Initializing orchestrator pool and request queue...")

    # Create multiple orchestrator instances
    num_orchestrator_instances = 2
    logger.info(f"Creating {num_orchestrator_instances} orchestrator instances.")

    async with AsyncSessionLocal() as db_session:
        for i in range(num_orchestrator_instances):
            logger.info(f"Creating orchestrator instance {i+1}...")
            orchestrator_instance = create_orchestrator(db_session)
            logger.info(f"Orchestrator instance {i+1} created successfully")

            await orchestrator_pool.add_instance(
                f"orchestrator_{i+1}", orchestrator_instance
            )
            logger.info(f"Orchestrator instance {i+1} added to pool")

    # Start health checks for orchestrator pool
    await orchestrator_pool.start_health_checks()
    logger.info("Orchestrator health checks started.")

    # Start background task for processing queued requests
    # Use global instances instead of creating new ones
    asyncio.create_task(_process_request_queue(orchestrator_pool, request_queue))
    logger.info("Background request processing task started.")

    # Start alert checker and system metrics collection
    if settings.ENVIRONMENT != "test":
        start_alert_checker()
        logger.info("Alert checker started.")

        # Start periodic system metrics collection
        async def collect_system_metrics_periodic():
            while True:
                try:
                    record_system_metrics()
                    await asyncio.sleep(60)  # Collect every minute
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {e}")
                    await asyncio.sleep(60)

        asyncio.create_task(collect_system_metrics_periodic())
        logger.info("System metrics collection started.")

    logger.info(
        "Application startup complete. Orchestrator pool and request queue initialized."
    )
    yield

    # Cleanup on shutdown
    logger.info("Application shutdown initiated.")
    await orchestrator_pool.shutdown()
    await cache_manager.disconnect()
    if hasattr(app.state, "request_queue_consumer_task"):
        app.state.request_queue_consumer_task.cancel()
        try:
            await app.state.request_queue_consumer_task
        except asyncio.CancelledError:
            pass
    logger.info("Application shutdown complete.")


# Initialize DI container
container = Container()
container.config.from_dict(
    {"llm_api_key": settings.LLM_API_KEY, "database_url": settings.DATABASE_URL}
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Add middleware in order of execution
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware)
app.add_middleware(RequestLoggingMiddleware, log_body=False, log_headers=True)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CustomCORSMiddleware,
    allowed_origins=["*"],
    allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(AuthMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)


# Exception handlers
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """Handle custom exceptions"""
    log_exception_with_context(
        exc,
        {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,  # Will be overridden by ErrorHandlingMiddleware
        content=exc.to_dict(),
    )


@app.exception_handler(APIException)
async def api_v2_exception_handler(request: Request, exc: APIException):
    """Handle API v2 exceptions"""
    log_exception_with_context(
        exc,
        {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorDetail(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ).dict(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    # Convert system exception to custom exception
    custom_exc = convert_system_exception(exc)

    log_exception_with_context(
        custom_exc,
        {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path,
            "method": request.method,
            "original_exception": str(exc),
        },
    )

    return JSONResponse(status_code=500, content=custom_exc.to_dict())


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    logger.warning(
        "not_found",
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else "unknown",
    )

    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource {request.url.path} was not found",
            "error_code": "NOT_FOUND",
        },
    )


# Background task for processing request queue
async def _process_request_queue(pool, queue):
    """Background task to process queued requests"""
    logger.info("Starting request queue processor")

    while True:
        try:
            # Get next request from queue using the correct method
            request_data = await queue.dequeue_request()

            if request_data is None:  # No requests available
                await asyncio.sleep(1)  # Brief pause before checking again
                continue

            # Process request with available orchestrator
            orchestrator = await pool.get_available_instance()
            if orchestrator:
                try:
                    # Convert QueuedRequest to dict format expected by orchestrator
                    request_dict = {
                        "id": request_data.id,
                        "user_command": request_data.user_command,
                        "session_id": request_data.session_id,
                        "file_info": request_data.file_info,
                        "agent_states": request_data.agent_states,
                    }

                    # Process the request
                    response = await orchestrator.process_request(request_dict)
                    # Handle response (e.g., send to WebSocket, store in database, etc.)
                    logger.info(
                        "Request processed successfully", request_id=request_data.id
                    )
                except Exception as e:
                    logger.error(
                        "Error processing queued request",
                        error=str(e),
                        request_id=request_data.id,
                    )
                    # Requeue the request if it failed
                    await queue.requeue_request(request_data, str(e))
            else:
                logger.warning(
                    "No available orchestrator for queued request",
                    request_id=request_data.id,
                )
                # Requeue the request if no orchestrator available
                await queue.requeue_request(request_data, "No orchestrator available")

        except asyncio.CancelledError:
            logger.info("Request queue processor cancelled")
            break
        except Exception as e:
            logger.error("Unexpected error in request queue processor", error=str(e))
            await asyncio.sleep(1)  # Brief pause before retrying


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    import time

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["Health"])
async def ready_check():
    """Readiness check - verifies all components are ready"""
    try:
        # Check database connection
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))

        # Check orchestrator pool health
        pool_health = await orchestrator_pool.get_health_status()

        # Check if any orchestrators are available
        available_orchestrators = [
            status for status in pool_health.values() if status["is_healthy"]
        ]

        # Check cache health
        cache_health = await cache_manager.health_check()

        if not available_orchestrators:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "No healthy orchestrators available",
                    "orchestrator_health": pool_health,
                    "cache_health": cache_health,
                },
            )

        return {
            "status": "ready",
            "database": "connected",
            "orchestrator_pool": pool_health,
            "available_orchestrators": len(available_orchestrators),
            "cache": "connected" if cache_health else "disconnected",
        }

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "reason": str(e)}
        )


# Test endpoint for long-running tasks
@app.post("/api/v1/long-task")
async def long_task(background_tasks: BackgroundTasks):
    """Test endpoint for long-running tasks"""

    def do_long_work():
        import time

        time.sleep(5)  # Simulate long work
        logger.info("Long task completed")

    background_tasks.add_task(do_long_work)
    return {"message": "Long task started", "task_id": str(uuid.uuid4())}


# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint with basic API information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.ENVIRONMENT == "development" else None,
        "health_check": "/health",
        "ready_check": "/ready",
    }


# Test endpoint for error handling
@app.get("/raise_error")
def raise_error(type: str = "value"):
    """Test endpoint for error handling"""
    if type == "value":
        raise ValueError("Test value error")
    elif type == "custom":
        from .core.exceptions import ValidationError

        raise ValidationError("Test custom error", field="test_field")
    else:
        raise Exception("Test generic error")


# Include routers
app.include_router(agents.router, tags=["Agents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(food.router, prefix="/api/v1/food", tags=["Food"])
app.include_router(pantry.router, prefix="/api/v1/pantry", tags=["Pantry"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(receipts.router, prefix="/api/v1/receipts", tags=["Receipts"])

# API v2
api_v2_router = APIRouter(prefix="/api/v2")
api_v2_router.include_router(receipts_v2.router)
api_v2_router.include_router(rag_v2.router)
api_v2_router.include_router(weather_v2.router)
app.include_router(api_v2_router)

# Include backup management router
from backend.api.v2.endpoints import backup

app.include_router(backup.router, prefix="/api/v2", tags=["Backup Management"])

from backend.core.alerting import (
    alert_manager,
    record_system_metrics,
    start_alert_checker,
)
from backend.core.prometheus_metrics import get_metrics, get_metrics_dict

# Import telemetry modules
from backend.core.telemetry import instrument_fastapi, setup_telemetry

# Setup telemetry
if settings.ENVIRONMENT != "test":
    setup_telemetry(
        service_name="foodsave-ai-backend",
        enable_jaeger=settings.ENVIRONMENT == "development",
        enable_prometheus=True,
        enable_console=settings.ENVIRONMENT == "development",
    )
    instrument_fastapi(app)


# Metrics endpoints
@app.get("/metrics", tags=["Monitoring"])
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    from prometheus_client import CONTENT_TYPE_LATEST

    return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/metrics", tags=["Monitoring"])
async def metrics_api():
    """JSON metrics endpoint for API consumption"""
    return {
        "metrics": get_metrics_dict(),
        "timestamp": asyncio.get_event_loop().time(),
        "service": "foodsave-ai-backend",
    }


@app.get("/api/v1/status", tags=["Monitoring"])
async def detailed_status():
    """Detailed system status with all components"""
    try:
        # System metrics
        from backend.core.prometheus_metrics import MetricsCollector

        metrics_collector = MetricsCollector()
        metrics_collector.collect_system_metrics()

        # Database health
        db_health = await check_database_health()

        # Orchestrator pool health
        pool_health = await orchestrator_pool.get_health_status()

        # Cache health
        cache_health = await cache_manager.health_check()

        # LLM status
        from backend.core.hybrid_llm_client import hybrid_llm_client

        llm_status = hybrid_llm_client.get_models_status()

        # Vector store status
        from backend.core.vector_store import vector_store

        vector_status = {
            "index_type": vector_store.index_type,
            "vector_count": (
                len(vector_store.documents) if hasattr(vector_store, "documents") else 0
            ),
        }

        return {
            "status": "operational",
            "timestamp": asyncio.get_event_loop().time(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "components": {
                "database": db_health,
                "orchestrator_pool": pool_health,
                "cache": {"connected": cache_health},
                "llm_models": llm_status,
                "vector_store": vector_status,
            },
            "metrics": get_metrics_dict(),
        }

    except Exception as e:
        logger.error("Detailed status check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            },
        )


# Alert endpoints
@app.get("/api/v1/alerts", tags=["Monitoring"])
async def get_alerts():
    """Get all active alerts"""
    return {
        "active_alerts": [
            {
                "id": alert.id,
                "rule_name": alert.rule.name,
                "severity": alert.rule.severity.value,
                "value": alert.value,
                "threshold": alert.rule.threshold,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status.value,
            }
            for alert in alert_manager.get_active_alerts()
        ],
        "stats": alert_manager.get_alert_stats(),
    }


@app.get("/api/v1/alerts/history", tags=["Monitoring"])
async def get_alert_history(hours: int = 24):
    """Get alert history for last N hours"""
    return {
        "alerts": [
            {
                "id": alert.id,
                "rule_name": alert.rule.name,
                "severity": alert.rule.severity.value,
                "value": alert.value,
                "threshold": alert.rule.threshold,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status.value,
                "acknowledged_by": alert.acknowledged_by,
                "resolved_at": (
                    alert.resolved_at.isoformat() if alert.resolved_at else None
                ),
            }
            for alert in alert_manager.get_alert_history(hours)
        ]
    }


@app.post("/api/v1/alerts/{rule_name}/acknowledge", tags=["Monitoring"])
async def acknowledge_alert(rule_name: str, user: str = "admin"):
    """Acknowledge an alert"""
    alert_manager.acknowledge_alert(rule_name, user)
    return {"message": f"Alert {rule_name} acknowledged by {user}"}


@app.post("/api/v1/alerts/{rule_name}/resolve", tags=["Monitoring"])
async def resolve_alert(rule_name: str):
    """Resolve an alert"""
    alert_manager.resolve_alert(rule_name)
    return {"message": f"Alert {rule_name} resolved"}


@app.post("/api/v1/alerts/rules", tags=["Monitoring"])
async def add_alert_rule(rule_data: dict):
    """Add a new alert rule"""
    from backend.core.alerting import AlertRule, AlertSeverity

    rule = AlertRule(
        name=rule_data["name"],
        description=rule_data["description"],
        metric_name=rule_data["metric_name"],
        threshold=rule_data["threshold"],
        operator=rule_data["operator"],
        severity=AlertSeverity(rule_data["severity"]),
        duration=rule_data.get("duration", 60),
        cooldown=rule_data.get("cooldown", 300),
    )

    alert_manager.add_rule(rule)
    return {"message": f"Alert rule {rule.name} added"}


@app.delete("/api/v1/alerts/rules/{rule_name}", tags=["Monitoring"])
async def remove_alert_rule(rule_name: str):
    """Remove an alert rule"""
    alert_manager.remove_rule(rule_name)
    return {"message": f"Alert rule {rule_name} removed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
