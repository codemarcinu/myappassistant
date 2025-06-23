"""
✅ REQUIRED: Performance monitoring and metrics collection
This module provides comprehensive monitoring for FoodSave AI application.
"""

import asyncio
import gc
import logging
import os
import time
import tracemalloc
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from weakref import WeakSet

import psutil
import structlog

from backend.core.telemetry import get_tracer

# Prometheus metrics
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Fallback mock classes
    class MockMetric:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

    Counter = Histogram = Gauge = Summary = MockMetric

logger = structlog.get_logger(__name__)


@dataclass
class MemorySnapshot:
    """Snapshot pamięci z tracemalloc"""

    timestamp: float
    memory_usage: int  # bytes
    peak_memory: int  # bytes
    top_allocations: List[Tuple[str, int]]  # (traceback, size)


@dataclass
class PerformanceMetrics:
    """✅ REQUIRED: Performance metrics collection for FoodSave AI"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        if PROMETHEUS_AVAILABLE:
            # Request metrics
            self.request_count = Counter(
                "foodsave_requests_total",
                "Total requests",
                ["method", "endpoint", "status"],
            )
            self.request_duration = Histogram(
                "foodsave_request_duration_seconds",
                "Request duration",
                ["method", "endpoint"],
            )

            # Agent metrics
            self.agent_request_count = Counter(
                "foodsave_agent_requests_total",
                "Total agent requests",
                ["agent_type", "status"],
            )
            self.agent_response_time = Histogram(
                "foodsave_agent_response_time_seconds",
                "Agent response time",
                ["agent_type"],
            )
            self.active_agents = Gauge(
                "foodsave_active_agents", "Number of active agents", ["agent_type"]
            )

            # Database metrics
            self.db_query_count = Counter(
                "foodsave_db_queries_total",
                "Total database queries",
                ["operation", "table"],
            )
            self.db_query_duration = Histogram(
                "foodsave_db_query_duration_seconds",
                "Database query duration",
                ["operation", "table"],
            )
            self.db_connections = Gauge(
                "foodsave_db_connections_active", "Active database connections"
            )

            # External API metrics
            self.external_api_calls = Counter(
                "foodsave_external_api_calls_total",
                "Total external API calls",
                ["api_name", "endpoint", "status"],
            )
            self.external_api_duration = Histogram(
                "foodsave_external_api_duration_seconds",
                "External API call duration",
                ["api_name", "endpoint"],
            )

            # System metrics
            self.memory_usage = Gauge(
                "foodsave_memory_usage_bytes", "Memory usage in bytes"
            )
            self.cpu_usage = Gauge("foodsave_cpu_usage_percent", "CPU usage percentage")

            # Error metrics
            self.error_count = Counter(
                "foodsave_errors_total", "Total errors", ["error_type", "component"]
            )

            # Processing metrics
            self.food_items_processed = Counter(
                "foodsave_food_items_processed_total",
                "Total food items processed",
                ["operation", "status"],
            )
            self.processing_duration = Histogram(
                "foodsave_processing_duration_seconds",
                "Food processing duration",
                ["operation"],
            )
        else:
            logger.warning("Prometheus client not available, using mock metrics")
            self.request_count = Counter()
            self.request_duration = Histogram()
            self.agent_request_count = Counter()
            self.agent_response_time = Histogram()
            self.active_agents = Gauge()
            self.db_query_count = Counter()
            self.db_query_duration = Histogram()
            self.db_connections = Gauge()
            self.external_api_calls = Counter()
            self.external_api_duration = Histogram()
            self.memory_usage = Gauge()
            self.cpu_usage = Gauge()
            self.error_count = Counter()
            self.food_items_processed = Counter()
            self.processing_duration = Histogram()


class MemoryProfiler:
    """Profiler pamięci z tracemalloc i psutil"""

    def __init__(self, enable_tracemalloc: bool = True) -> None:
        self.enable_tracemalloc = enable_tracemalloc
        self.process = psutil.Process()
        self.snapshots: List[MemorySnapshot] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        self._active_contexts: WeakSet = WeakSet()

        if enable_tracemalloc:
            tracemalloc.start(25)  # Track top 25 allocations

    def __enter__(self) -> None:
        """Context manager entry"""
        self._active_contexts.add(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit z cleanup"""
        self._active_contexts.discard(self)
        if self.enable_tracemalloc:
            tracemalloc.stop()

    def take_snapshot(self) -> MemorySnapshot:
        """Pobiera snapshot pamięci"""
        current, peak = tracemalloc.get_traced_memory()

        # Get top allocations
        top_allocations = []

        if self.enable_tracemalloc:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("lineno")[:10]
            top_allocations = [
                (f"{stat.traceback.format()}", stat.size) for stat in top_stats
            ]

        memory_snapshot = MemorySnapshot(
            timestamp=time.time(),
            memory_usage=current,
            peak_memory=peak,
            top_allocations=top_allocations,
        )

        self.snapshots.append(memory_snapshot)
        return memory_snapshot

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Pobiera metryki wydajności procesu"""
        with self.process.oneshot():
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=self.process.cpu_percent(),
                memory_percent=self.process.memory_percent(),
                memory_rss=self.process.memory_info().rss,
                memory_vms=self.process.memory_info().vms,
                open_files=len(self.process.open_files()),
                threads=self.process.num_threads(),
            )

        self.performance_metrics.append(metrics)
        return metrics

    def log_memory_usage(self, context: str = "general") -> None:
        """Loguje aktualne użycie pamięci"""
        snapshot = self.take_snapshot()
        metrics = self.get_performance_metrics()

        logger.info(
            "memory_usage",
            context=context,
            memory_mb=snapshot.memory_usage / 1024 / 1024,
            peak_mb=snapshot.peak_memory / 1024 / 1024,
            cpu_percent=metrics.cpu_percent,
            memory_percent=metrics.memory_percent,
            rss_mb=metrics.memory_rss / 1024 / 1024,
        )

    def detect_memory_leak(self, threshold_mb: float = 50.0) -> bool:
        """Wykrywa potencjalne wycieki pamięci"""
        if len(self.snapshots) < 2:
            return False

        first = self.snapshots[0]
        last = self.snapshots[-1]

        memory_increase = (last.memory_usage - first.memory_usage) / 1024 / 1024

        if memory_increase > threshold_mb:
            logger.warning(
                "potential_memory_leak_detected",
                memory_increase_mb=memory_increase,
                threshold_mb=threshold_mb,
            )
            return True

        return False

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.snapshots.clear()
        self.performance_metrics.clear()
        gc.collect()


class AsyncMemoryProfiler(MemoryProfiler):
    """Asynchroniczny profiler pamięci"""

    async def take_snapshot_async(self) -> MemorySnapshot:
        """Asynchroniczne pobieranie snapshot"""
        return await asyncio.get_event_loop().run_in_executor(None, self.take_snapshot)

    async def get_performance_metrics_async(self) -> PerformanceMetrics:
        """Asynchroniczne pobieranie metryk"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_performance_metrics
        )

    async def log_memory_usage_async(self, context: str = "general") -> None:
        """Asynchroniczne logowanie pamięci"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.log_memory_usage, context
        )


@contextmanager
def memory_profiling_context(context_name: str = "operation") -> None:
    """Context manager dla memory profiling"""
    profiler = MemoryProfiler()
    try:
        profiler.log_memory_usage(f"{context_name}_start")
        yield profiler
    finally:
        profiler.log_memory_usage(f"{context_name}_end")
        if profiler.detect_memory_leak():
            logger.error(f"Memory leak detected in {context_name}")
        profiler.cleanup()


@asynccontextmanager
async def async_memory_profiling_context(context_name: str = "async_operation") -> None:
    """Async context manager dla memory profiling"""
    profiler = AsyncMemoryProfiler()
    try:
        await profiler.log_memory_usage_async(f"{context_name}_start")
        yield profiler
    finally:
        await profiler.log_memory_usage_async(f"{context_name}_end")
        if profiler.detect_memory_leak():
            logger.error(f"Memory leak detected in {context_name}")
        profiler.cleanup()


class MemoryMonitor:
    """Globalny monitor pamięci dla aplikacji"""

    def __init__(self) -> None:
        self.profilers: Dict[str, MemoryProfiler] = {}
        self.monitoring_enabled = (
            os.getenv("ENABLE_MEMORY_MONITORING", "true").lower() == "true"
        )

    def get_profiler(self, name: str) -> MemoryProfiler:
        """Pobiera lub tworzy profiler dla danego komponentu"""
        if name not in self.profilers:
            self.profilers[name] = MemoryProfiler()
        return self.profilers[name]

    def log_all_components(self) -> None:
        """Loguje pamięć dla wszystkich komponentów"""
        if not self.monitoring_enabled:
            return

        for name, profiler in self.profilers.items():
            profiler.log_memory_usage(name)

    def cleanup_all(self) -> None:
        """Cleanup wszystkich profilerów"""
        for profiler in self.profilers.values():
            profiler.cleanup()
        self.profilers.clear()


# Global instance
memory_monitor = MemoryMonitor()


def get_memory_profiler(name: str) -> MemoryProfiler:
    """Helper function do pobierania profilerów"""
    return memory_monitor.get_profiler(name)


def log_memory_usage(context: str = "general") -> None:
    """Helper function do logowania pamięci"""
    if memory_monitor.monitoring_enabled:
        profiler = get_memory_profiler(context)
        profiler.log_memory_usage(context)


# Global metrics instance
metrics = PerformanceMetrics()


def monitor_request(method: str, endpoint: str):
    """✅ REQUIRED: Monitor HTTP requests with proper metrics"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.error_count.labels(
                    error_type=type(e).__name__, component="http_request"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.request_count.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                metrics.request_duration.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.error_count.labels(
                    error_type=type(e).__name__, component="http_request"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.request_count.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                metrics.request_duration.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def monitor_agent(agent_type: str):
    """✅ REQUIRED: Monitor agent performance"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            # Increment active agents
            metrics.active_agents.labels(agent_type=agent_type).inc()

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.error_count.labels(
                    error_type=type(e).__name__, component=f"agent_{agent_type}"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.agent_request_count.labels(
                    agent_type=agent_type, status=status
                ).inc()
                metrics.agent_response_time.labels(agent_type=agent_type).observe(
                    duration
                )

                # Decrement active agents
                metrics.active_agents.labels(agent_type=agent_type).dec()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            # Increment active agents
            metrics.active_agents.labels(agent_type=agent_type).inc()

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.error_count.labels(
                    error_type=type(e).__name__, component=f"agent_{agent_type}"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.agent_request_count.labels(
                    agent_type=agent_type, status=status
                ).inc()
                metrics.agent_response_time.labels(agent_type=agent_type).observe(
                    duration
                )

                # Decrement active agents
                metrics.active_agents.labels(agent_type=agent_type).dec()

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def monitor_database_operation(operation: str, table: str = "unknown"):
    """✅ REQUIRED: Monitor database operations"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                metrics.db_query_count.labels(operation=operation, table=table).inc()
                return result
            except Exception as e:
                metrics.error_count.labels(
                    error_type=type(e).__name__, component="database"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.db_query_duration.labels(
                    operation=operation, table=table
                ).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                metrics.db_query_count.labels(operation=operation, table=table).inc()
                return result
            except Exception as e:
                metrics.error_count.labels(
                    error_type=type(e).__name__, component="database"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.db_query_duration.labels(
                    operation=operation, table=table
                ).observe(duration)

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def monitor_external_api(api_name: str, endpoint: str):
    """✅ REQUIRED: Monitor external API calls"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.error_count.labels(
                    error_type=type(e).__name__, component=f"external_api_{api_name}"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.external_api_calls.labels(
                    api_name=api_name, endpoint=endpoint, status=status
                ).inc()
                metrics.external_api_duration.labels(
                    api_name=api_name, endpoint=endpoint
                ).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.error_count.labels(
                    error_type=type(e).__name__, component=f"external_api_{api_name}"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.external_api_calls.labels(
                    api_name=api_name, endpoint=endpoint, status=status
                ).inc()
                metrics.external_api_duration.labels(
                    api_name=api_name, endpoint=endpoint
                ).observe(duration)

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@asynccontextmanager
async def monitor_processing(operation: str):
    """✅ REQUIRED: Monitor food processing operations"""
    start_time = time.time()
    status = "success"

    try:
        yield
    except Exception as e:
        status = "error"
        metrics.error_count.labels(
            error_type=type(e).__name__, component="food_processing"
        ).inc()
        raise
    finally:
        duration = time.time() - start_time
        metrics.processing_duration.labels(operation=operation).observe(duration)


def update_system_metrics():
    """✅ REQUIRED: Update system metrics (memory, CPU)"""
    try:
        import psutil

        # Memory usage
        memory_info = psutil.virtual_memory()
        metrics.memory_usage.set(memory_info.used)

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.cpu_usage.set(cpu_percent)

    except ImportError:
        logger.warning("psutil not available, skipping system metrics")
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")


def record_food_item_processed(operation: str, status: str = "success"):
    """Record food item processing"""
    metrics.food_items_processed.labels(operation=operation, status=status).inc()


def record_error(error_type: str, component: str):
    """Record error occurrence"""
    metrics.error_count.labels(error_type=error_type, component=component).inc()


def get_metrics_summary() -> Dict[str, Any]:
    """Get summary of current metrics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "metrics_collected": {
            "requests": "request_count, request_duration",
            "agents": "agent_request_count, agent_response_time, active_agents",
            "database": "db_query_count, db_query_duration, db_connections",
            "external_apis": "external_api_calls, external_api_duration",
            "system": "memory_usage, cpu_usage",
            "errors": "error_count",
            "processing": "food_items_processed, processing_duration",
        },
    }
