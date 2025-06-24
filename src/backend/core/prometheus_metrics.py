"""
Prometheus Metrics dla FoodSave AI Backend
Zgodnie z regułami MDC dla monitoringu i observability
"""

import time
from typing import Any, Dict

import psutil
import structlog
from prometheus_client import (CollectorRegistry, Counter, Gauge, Histogram,
                               generate_latest)

logger = structlog.get_logger(__name__)

# Global registry
registry = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Agent metrics
AGENT_REQUEST_COUNT = Counter(
    "agent_requests_total",
    "Total number of agent requests",
    ["agent_type", "status"],
    registry=registry,
)

AGENT_PROCESSING_TIME = Histogram(
    "agent_processing_time_seconds",
    "Agent processing time in seconds",
    ["agent_type"],
    registry=registry,
)

AGENT_MEMORY_USAGE = Gauge(
    "agent_memory_usage_bytes",
    "Agent memory usage in bytes",
    ["agent_type"],
    registry=registry,
)

# Database metrics
DB_QUERY_COUNT = Counter(
    "database_queries_total",
    "Total number of database queries",
    ["operation", "table"],
    registry=registry,
)

DB_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    registry=registry,
)

DB_CONNECTION_POOL_SIZE = Gauge(
    "database_connection_pool_size",
    "Database connection pool size",
    ["state"],
    registry=registry,
)

# LLM metrics
LLM_REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["model", "status"],
    registry=registry,
)

LLM_REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["model"],
    registry=registry,
)

LLM_TOKENS_USED = Counter(
    "llm_tokens_total",
    "Total number of tokens used",
    ["model", "type"],
    registry=registry,
)

# Vector store metrics
VECTOR_SEARCH_COUNT = Counter(
    "vector_search_total",
    "Total number of vector searches",
    ["index_type"],
    registry=registry,
)

VECTOR_SEARCH_DURATION = Histogram(
    "vector_search_duration_seconds",
    "Vector search duration in seconds",
    ["index_type"],
    registry=registry,
)

VECTOR_STORE_SIZE = Gauge(
    "vector_store_size", "Number of vectors in store", ["index_type"], registry=registry
)

# OCR metrics
OCR_PROCESSING_COUNT = Counter(
    "ocr_processing_total",
    "Total number of OCR processing operations",
    ["file_type", "status"],
    registry=registry,
)

OCR_PROCESSING_DURATION = Histogram(
    "ocr_processing_duration_seconds",
    "OCR processing duration in seconds",
    ["file_type"],
    registry=registry,
)

# System metrics
SYSTEM_MEMORY_USAGE = Gauge(
    "system_memory_usage_bytes",
    "System memory usage in bytes",
    ["type"],
    registry=registry,
)

SYSTEM_CPU_USAGE = Gauge(
    "system_cpu_usage_percent", "System CPU usage percentage", registry=registry
)

SYSTEM_DISK_USAGE = Gauge(
    "system_disk_usage_bytes",
    "System disk usage in bytes",
    ["mount_point"],
    registry=registry,
)

# Cache metrics
CACHE_HIT_COUNT = Counter(
    "cache_hits_total", "Total number of cache hits", ["cache_type"], registry=registry
)

CACHE_MISS_COUNT = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
    registry=registry,
)

CACHE_SIZE = Gauge(
    "cache_size", "Cache size in items", ["cache_type"], registry=registry
)

# Circuit breaker metrics
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["breaker_name"],
    registry=registry,
)

CIRCUIT_BREAKER_FAILURES = Counter(
    "circuit_breaker_failures_total",
    "Total number of circuit breaker failures",
    ["breaker_name"],
    registry=registry,
)


class MetricsCollector:
    """Collector dla system metrics"""

    def __init__(self) -> None:
        self.process = psutil.Process()

    def collect_system_metrics(self) -> None:
        """Collect system metrics"""
        try:
            # Memory metrics
            memory_info = self.process.memory_info()
            SYSTEM_MEMORY_USAGE.labels(type="rss").set(memory_info.rss)
            SYSTEM_MEMORY_USAGE.labels(type="vms").set(memory_info.vms)

            # CPU metrics
            cpu_percent = self.process.cpu_percent()
            SYSTEM_CPU_USAGE.set(cpu_percent)

            # Disk metrics
            disk_usage = psutil.disk_usage("/")
            SYSTEM_DISK_USAGE.labels(mount_point="/").set(disk_usage.used)

        except Exception:
            logger.error("Error collecting system metrics", exc_info=True)


class MetricsMiddleware:
    """Middleware dla collecting metrics"""

    def __init__(self, app) -> None:
        self.app = app
        self.metrics_collector = MetricsCollector()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            start_time = time.time()
            method = scope["method"]
            path = scope["path"]

            # Increment request count
            REQUEST_COUNT.labels(method=method, endpoint=path, status="started").inc()

            # Process request
            try:
                await self.app(scope, receive, send)
                status = "success"
            except Exception:
                status = "error"
                raise
            finally:
                # Record duration
                duration = time.time() - start_time
                REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

                # Increment final request count
                REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()


def record_agent_metrics(
    agent_type: str, success: bool, duration: float, memory_usage: int | None = None
) -> None:
    """Record agent performance metrics"""
    status = "success" if success else "error"
    AGENT_REQUEST_COUNT.labels(agent_type=agent_type, status=status).inc()
    AGENT_PROCESSING_TIME.labels(agent_type=agent_type).observe(duration)
    if memory_usage is not None:
        AGENT_MEMORY_USAGE.labels(agent_type=agent_type).set(memory_usage)


def record_db_metrics(operation: str, table: str, duration: float) -> None:
    """Record database metrics"""
    DB_QUERY_COUNT.labels(operation=operation, table=table).inc()
    DB_QUERY_DURATION.labels(operation=operation, table=table).observe(duration)


def record_llm_metrics(
    model: str,
    success: bool,
    duration: float,
    tokens: int | None = None,
    token_type: str = "total",
) -> None:
    """Record LLM performance metrics"""
    status = "success" if success else "error"
    LLM_REQUEST_COUNT.labels(model=model, status=status).inc()
    LLM_REQUEST_DURATION.labels(model=model).observe(duration)
    if tokens is not None:
        LLM_TOKENS_USED.labels(model=model, type=token_type).inc(tokens)


def record_vector_metrics(
    index_type: str, duration: float, store_size: int | None = None
) -> None:
    """Record vector store performance metrics"""
    VECTOR_SEARCH_COUNT.labels(index_type=index_type).inc()
    VECTOR_SEARCH_DURATION.labels(index_type=index_type).observe(duration)
    if store_size is not None:
        VECTOR_STORE_SIZE.labels(index_type=index_type).set(store_size)


def record_ocr_metrics(file_type: str, success: bool, duration: float) -> None:
    """Record OCR metrics"""
    status = "success" if success else "error"
    OCR_PROCESSING_COUNT.labels(file_type=file_type, status=status).inc()
    OCR_PROCESSING_DURATION.labels(file_type=file_type).observe(duration)


def record_cache_metrics(cache_type: str, hit: bool) -> None:
    """Record cache metrics"""
    if hit:
        CACHE_HIT_COUNT.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISS_COUNT.labels(cache_type=cache_type).inc()


def record_circuit_breaker_metrics(
    breaker_name: str, state: str, failure: bool = False
) -> None:
    """Record circuit breaker metrics"""
    state_map = {"closed": 0, "open": 1, "half_open": 2}
    CIRCUIT_BREAKER_STATE.labels(breaker_name=breaker_name).set(
        state_map.get(state, -1)
    )
    if failure:
        CIRCUIT_BREAKER_FAILURES.labels(breaker_name=breaker_name).inc()


def get_metrics() -> bytes:
    """Generate latest metrics for Prometheus endpoint"""
    return generate_latest(registry)


def get_metrics_dict() -> Dict[str, Any]:
    """Generate latest metrics as a dictionary"""
    metrics_text = get_metrics().decode("utf-8")
    metrics_dict = {}
    for line in metrics_text.strip().split("\n"):
        if not line.startswith("#"):
            parts = line.split(" ")
            key = parts[0]
            value = parts[1]
            metrics_dict[key] = value
    return metrics_dict
