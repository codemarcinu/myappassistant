"""
Memory and Performance Monitoring Module
Zgodnie z regułami MDC dla zarządzania pamięcią i monitoringu
"""

import asyncio
import gc
import os
import time
import tracemalloc
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import List, Tuple
from weakref import WeakSet

import psutil
import structlog

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
    """Metryki wydajności"""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # bytes
    memory_vms: int  # bytes
    open_files: int
    threads: int


class MemoryProfiler:
    """Profiler pamięci z tracemalloc i psutil"""

    def __init__(self, enable_tracemalloc: bool = True):
        self.enable_tracemalloc = enable_tracemalloc
        self.process = psutil.Process()
        self.snapshots: List[MemorySnapshot] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        self._active_contexts: WeakSet = WeakSet()

        if enable_tracemalloc:
            tracemalloc.start(25)  # Track top 25 allocations

    def __enter__(self):
        """Context manager entry"""
        self._active_contexts.add(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit z cleanup"""
        self._active_contexts.discard(self)
        if self.enable_tracemalloc:
            tracemalloc.stop()

    def take_snapshot(self) -> MemorySnapshot:
        """Pobiera snapshot pamięci"""
        current, peak = tracemalloc.get_traced_memory()

        # Get top allocations
        top_stats = tracemalloc.get_traced_memory()
        top_allocations = []

        if self.enable_tracemalloc:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("lineno")[:10]
            top_allocations = [
                (f"{stat.traceback.format()}", stat.size) for stat in top_stats
            ]

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            memory_usage=current,
            peak_memory=peak,
            top_allocations=top_allocations,
        )

        self.snapshots.append(snapshot)
        return snapshot

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

    def log_memory_usage(self, context: str = "general"):
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

    def cleanup(self):
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

    async def log_memory_usage_async(self, context: str = "general"):
        """Asynchroniczne logowanie pamięci"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.log_memory_usage, context
        )


@contextmanager
def memory_profiling_context(context_name: str = "operation"):
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
async def async_memory_profiling_context(context_name: str = "async_operation"):
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

    def __init__(self):
        self.profilers: Dict[str, MemoryProfiler] = {}
        self.monitoring_enabled = (
            os.getenv("ENABLE_MEMORY_MONITORING", "true").lower() == "true"
        )

    def get_profiler(self, name: str) -> MemoryProfiler:
        """Pobiera lub tworzy profiler dla danego komponentu"""
        if name not in self.profilers:
            self.profilers[name] = MemoryProfiler()
        return self.profilers[name]

    def log_all_components(self):
        """Loguje pamięć dla wszystkich komponentów"""
        if not self.monitoring_enabled:
            return

        for name, profiler in self.profilers.items():
            profiler.log_memory_usage(name)

    def cleanup_all(self):
        """Cleanup wszystkich profilerów"""
        for profiler in self.profilers.values():
            profiler.cleanup()
        self.profilers.clear()


# Global instance
memory_monitor = MemoryMonitor()


def get_memory_profiler(name: str) -> MemoryProfiler:
    """Helper function do pobierania profilerów"""
    return memory_monitor.get_profiler(name)


def log_memory_usage(context: str = "general"):
    """Helper function do logowania pamięci"""
    if memory_monitor.monitoring_enabled:
        profiler = get_memory_profiler(context)
        profiler.log_memory_usage(context)
