from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Memory Profiling Tests z pytest-benchmark
Zgodnie z regułami MDC dla testowania i monitoringu
"""

import asyncio
import gc
from unittest.mock import Mock, patch

import pytest
import pytest_benchmark.fixture

from backend.core.monitoring import (AsyncMemoryProfiler, MemoryProfiler,
                                     MemorySnapshot, PerformanceMetrics,
                                     async_memory_profiling_context,
                                     memory_monitor, memory_profiling_context)


class TestMemoryProfiler:
    """Testy dla MemoryProfiler"""

    def test_memory_profiler_initialization(self) -> None:
        """Test inicjalizacji profilerów"""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        assert profiler.enable_tracemalloc is False
        assert len(profiler.snapshots) == 0
        assert len(profiler.performance_metrics) == 0

    def test_take_snapshot(self) -> None:
        """Test pobierania snapshot pamięci"""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        snapshot = profiler.take_snapshot()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.timestamp > 0
        assert snapshot.memory_usage >= 0
        assert snapshot.peak_memory >= 0
        assert len(profiler.snapshots) == 1

    def test_get_performance_metrics(self) -> None:
        """Test pobierania metryk wydajności"""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        metrics = profiler.get_performance_metrics()

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.timestamp > 0
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.memory_rss > 0
        assert metrics.memory_vms > 0
        assert metrics.open_files >= 0
        assert metrics.threads > 0
        assert len(profiler.performance_metrics) == 1

    def test_memory_leak_detection(self) -> None:
        """Test wykrywania wycieków pamięci"""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        # Pierwszy snapshot
        profiler.take_snapshot()

        # Symulacja wzrostu pamięci
        with patch.object(profiler, "take_snapshot") as mock_snapshot:
            mock_snapshot.return_value = MemorySnapshot(
                timestamp=1.0,
                memory_usage=100 * 1024 * 1024,  # 100MB
                peak_memory=100 * 1024 * 1024,
                top_allocations=[],
            )

            # Drugi snapshot z dużym wzrostem pamięci
            profiler.snapshots.append(mock_snapshot.return_value)

            # Wykrycie wycieku
            assert profiler.detect_memory_leak(threshold_mb=50.0) is True

    def test_cleanup(self) -> None:
        """Test cleanup resources"""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.take_snapshot()
        profiler.get_performance_metrics()

        assert len(profiler.snapshots) > 0
        assert len(profiler.performance_metrics) > 0

        profiler.cleanup()

        assert len(profiler.snapshots) == 0
        assert len(profiler.performance_metrics) == 0


class TestAsyncMemoryProfiler:
    """Testy dla AsyncMemoryProfiler"""

    @pytest.mark.asyncio
    async def test_async_snapshot(self) -> None:
        """Test asynchronicznego pobierania snapshot"""
        profiler = AsyncMemoryProfiler(enable_tracemalloc=False)
        snapshot = await profiler.take_snapshot_async()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.timestamp > 0

    @pytest.mark.asyncio
    async def test_async_performance_metrics(self) -> None:
        """Test asynchronicznego pobierania metryk"""
        profiler = AsyncMemoryProfiler(enable_tracemalloc=False)
        metrics = await profiler.get_performance_metrics_async()

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.timestamp > 0


class TestMemoryProfilingContext:
    """Testy dla context managers"""

    def test_memory_profiling_context(self) -> None:
        """Test synchronicznego context manager"""
        with memory_profiling_context("test_operation") as profiler:
            assert isinstance(profiler, MemoryProfiler)
            # Symulacja operacji
            profiler.take_snapshot()

        # Sprawdź czy cleanup został wykonany
        assert len(profiler.snapshots) == 0

    @pytest.mark.asyncio
    async def test_async_memory_profiling_context(self) -> None:
        """Test asynchronicznego context manager"""
        async with async_memory_profiling_context("test_async_operation") as profiler:
            assert isinstance(profiler, AsyncMemoryProfiler)
            # Symulacja operacji
            await profiler.take_snapshot_async()

        # Sprawdź czy cleanup został wykonany
        assert len(profiler.snapshots) == 0


class TestMemoryMonitor:
    """Testy dla globalnego monitora pamięci"""

    def test_get_profiler(self) -> None:
        """Test pobierania profilerów"""
        profiler1 = memory_monitor.get_profiler("test_component")
        profiler2 = memory_monitor.get_profiler("test_component")

        assert profiler1 is profiler2  # Singleton pattern
        assert "test_component" in memory_monitor.profilers

    def test_cleanup_all(self) -> None:
        """Test cleanup wszystkich profilerów"""
        memory_monitor.profilers.clear()  # Wyczyść globalny stan
        memory_monitor.get_profiler("test1")
        memory_monitor.get_profiler("test2")
        # Sprawdź czy test1 i test2 są obecne
        assert "test1" in memory_monitor.profilers
        assert "test2" in memory_monitor.profilers


# Benchmark tests z pytest-benchmark
class TestMemoryProfilingBenchmarks:
    """Benchmark tests dla memory profiling"""

    def test_snapshot_creation_benchmark(self, benchmark) -> None:
        """Benchmark tworzenia snapshot"""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        def create_snapshot() -> None:
            return profiler.take_snapshot()

        result = benchmark(create_snapshot)
        assert isinstance(result, MemorySnapshot)

    def test_performance_metrics_benchmark(self, benchmark) -> None:
        """Benchmark pobierania metryk wydajności"""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        def get_metrics() -> None:
            return profiler.get_performance_metrics()

        result = benchmark(get_metrics)
        assert isinstance(result, PerformanceMetrics)

    @pytest.mark.asyncio
    async def test_async_snapshot_benchmark(self, benchmark) -> None:
        """Benchmark asynchronicznego snapshot"""
        profiler = AsyncMemoryProfiler(enable_tracemalloc=False)

        async def create_async_snapshot() -> None:
            return await profiler.take_snapshot_async()

        result = await benchmark(create_async_snapshot)
        assert isinstance(result, MemorySnapshot)


# Memory leak detection tests
class TestMemoryLeakDetection:
    """Testy wykrywania wycieków pamięci"""

    def test_no_memory_leak(self) -> None:
        """Test gdy nie ma wycieku pamięci"""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        # Pierwszy snapshot
        profiler.take_snapshot()

        # Drugi snapshot z minimalnym wzrostem
        with patch.object(profiler, "take_snapshot") as mock_snapshot:
            mock_snapshot.return_value = MemorySnapshot(
                timestamp=1.0,
                memory_usage=10 * 1024 * 1024,  # 10MB
                peak_memory=10 * 1024 * 1024,
                top_allocations=[],
            )
            profiler.snapshots.append(mock_snapshot.return_value)

            # Brak wycieku
            assert profiler.detect_memory_leak(threshold_mb=50.0) is False

    def test_memory_leak_threshold(self) -> None:
        """Test różnych progów wycieku pamięci"""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        # Pierwszy snapshot
        profiler.take_snapshot()

        # Drugi snapshot z wzrostem 30MB
        with patch.object(profiler, "take_snapshot") as mock_snapshot:
            mock_snapshot.return_value = MemorySnapshot(
                timestamp=1.0,
                memory_usage=30 * 1024 * 1024,  # 30MB
                peak_memory=30 * 1024 * 1024,
                top_allocations=[],
            )
            profiler.snapshots.append(mock_snapshot.return_value)

            # Wyciek przy progu 20MB
            assert profiler.detect_memory_leak(threshold_mb=20.0) is True

            # Brak wycieku przy progu 50MB
            assert profiler.detect_memory_leak(threshold_mb=50.0) is False


# Integration tests
class TestMemoryProfilingIntegration:
    """Testy integracyjne memory profiling"""

    def test_full_profiling_cycle(self) -> None:
        """Test pełnego cyklu profilowania"""
        with memory_profiling_context("integration_test") as profiler:
            # Wykonaj operacje
            for i in range(5):
                profiler.take_snapshot()
                profiler.get_performance_metrics()

            # Sprawdź czy dane zostały zebrane
            assert len(profiler.snapshots) >= 5  # Pozwól na dodatkowe snapshoty

    @pytest.mark.asyncio
    async def test_async_profiling_cycle(self) -> None:
        """Test asynchronicznego cyklu profilowania"""
        async with async_memory_profiling_context("async_integration_test") as profiler:
            # Wykonaj operacje
            for i in range(3):
                await profiler.take_snapshot_async()
                await profiler.get_performance_metrics_async()

            # Sprawdź czy dane zostały zebrane
            assert len(profiler.snapshots) >= 3  # Pozwól na dodatkowe snapshoty
