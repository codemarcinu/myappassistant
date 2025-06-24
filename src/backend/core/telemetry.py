"""
OpenTelemetry Integration dla Distributed Tracing
Zgodnie z regułami MDC dla monitoringu i observability
"""

import os
from functools import wraps
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter)
from prometheus_client import start_http_server

from backend.config import settings

# Global tracer
tracer: Optional[trace.Tracer] = None


def setup_telemetry(
    service_name: str = "foodsave-ai-backend",
    enable_jaeger: bool = True,
    enable_prometheus: bool = True,
    enable_console: bool = False,
) -> None:
    """Setup OpenTelemetry dla distributed tracing i metrics"""
    global tracer

    # Resource configuration
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    # Trace provider setup
    trace_provider = TracerProvider(resource=resource)

    # Jaeger exporter
    if enable_jaeger:
        jaeger_endpoint = os.getenv(
            "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        )
        jaeger_exporter = JaegerExporter(
            collector_endpoint=jaeger_endpoint,
        )
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    # Console exporter (for development)
    if enable_console or settings.ENVIRONMENT == "development":
        console_exporter = ConsoleSpanExporter()
        trace_provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set global trace provider
    trace.set_tracer_provider(trace_provider)
    tracer = trace.get_tracer(__name__)

    # Metrics setup
    if enable_prometheus:
        setup_prometheus_metrics()


def setup_prometheus_metrics(port: int = 8001) -> None:
    """Setup Prometheus metrics exporter"""
    try:
        # Start Prometheus HTTP server
        start_http_server(port)
        print(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        print(f"Failed to start Prometheus server: {e}")


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument SQLAlchemy engine z OpenTelemetry"""
    SQLAlchemyInstrumentor.instrument(engine=engine)


def instrument_httpx() -> None:
    """Instrument HTTPX client z OpenTelemetry"""
    HTTPXClientInstrumentor.instrument()


def get_tracer() -> trace.Tracer:
    """Get global tracer instance"""
    global tracer
    if tracer is None:
        tracer = trace.get_tracer(__name__)
    return tracer


def create_span(name: str, attributes: Optional[dict] = None) -> trace.Span:
    """Create a new span with given name and attributes"""
    current_tracer = get_tracer()
    span = current_tracer.start_span(name, attributes=attributes or {})
    return span


def add_span_event(
    span: trace.Span, name: str, attributes: Optional[dict] = None
) -> None:
    """Add event to span"""
    span.add_event(name, attributes=attributes or {})


def set_span_attribute(span: trace.Span, key: str, value: Any) -> None:
    """Set attribute on span"""
    span.set_attribute(key, value)


def record_exception(span: trace.Span, exception: Exception) -> None:
    """Record exception in span"""
    span.record_exception(exception)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


# Context managers dla spans
class SpanContext:
    """Context manager dla spans"""

    def __init__(self, name: str, attributes: Optional[dict] = None) -> None:
        self.name = name
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self) -> "SpanContext":
        self.span = create_span(self.name, self.attributes)
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self.span:
            if exc_type:
                record_exception(self.span, exc_val)
            self.span.end()


# Decorator dla funkcji z tracing
def traced_function(
    name: str | None = None, attributes: Optional[dict] = None
) -> Callable[..., Any]:
    """Decorator to add tracing to functions"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = name or f"{func.__module__}.{func.__name__}"
            with SpanContext(span_name, attributes):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Async decorator
def traced_async_function(
    name: str | None = None, attributes: Optional[Dict[str, Any]] = None
) -> Callable[..., Any]:
    """Decorator to add tracing to async functions"""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = name or f"{func.__module__}.{func.__name__}"
            with SpanContext(span_name, attributes):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
