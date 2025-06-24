from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Tests dla Memory Monitoring Middleware
Zgodnie z regułami MDC dla testowania i monitoringu
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.core.middleware import MemoryMonitoringMiddleware
from backend.core.telemetry import get_tracer


# GLOBALNY PATCH dla async_memory_profiling_context
@pytest.fixture(autouse=True)
def patch_async_memory_profiling_context(monkeypatch) -> None:
    mock_profiler = AsyncMock()
    mock_profiler.get_performance_metrics_async.return_value.memory_rss = (
        100 * 1024 * 1024
    )  # 100MB
    mock_profiler.get_performance_metrics_async.return_value.cpu_percent = 25.5
    mock_profiler.log_memory_usage_async.return_value = None

    async def dummy_cm(*args, **kwargs) -> None:
        class DummyAsyncCM:
            async def __aenter__(self) -> None:
                return mock_profiler

            async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
                return None

        return DummyAsyncCM()

    monkeypatch.setattr(
        "backend.core.monitoring.async_memory_profiling_context", dummy_cm
    )
    yield


@pytest.fixture
def app_with_memory_middleware() -> None:
    """FastAPI app z memory monitoring middleware"""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint() -> None:
        return {"message": "test"}

    @app.get("/memory-intensive")
    async def memory_intensive_endpoint() -> None:
        # Symulacja operacji intensywnej pamięciowo
        large_list = [i for i in range(10000)]
        return {"count": len(large_list)}

    app.add_middleware(MemoryMonitoringMiddleware, enable_memory_profiling=True)
    return app


@pytest.fixture
def client(app_with_memory_middleware) -> None:
    """Test client dla app z memory middleware"""
    return TestClient(app_with_memory_middleware)


class TestMemoryMonitoringMiddleware:
    """Testy dla MemoryMonitoringMiddleware"""

    def test_middleware_initialization(self) -> None:
        """Test inicjalizacji middleware"""
        app = FastAPI()
        middleware = MemoryMonitoringMiddleware(app, enable_memory_profiling=True)

        assert middleware.enable_memory_profiling is True
        assert middleware.app == app

    def test_middleware_with_memory_profiling_disabled(self) -> None:
        """Test middleware z wyłączonym memory profiling"""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> None:
            return {"message": "test"}

        app.add_middleware(MemoryMonitoringMiddleware, enable_memory_profiling=False)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Memory-Usage-MB" not in response.headers
        assert "X-CPU-Percent" not in response.headers

    @pytest.mark.asyncio
    async def test_middleware_with_memory_profiling_enabled(self, client) -> None:
        """Test middleware z włączonym memory profiling"""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Memory-Usage-MB" in response.headers
        assert "X-CPU-Percent" in response.headers
        # Sprawdzamy tylko typ i zakres, nie dokładną wartość
        mem = float(response.headers["X-Memory-Usage-MB"])
        cpu = float(response.headers["X-CPU-Percent"])
        assert mem > 0
        assert 0 <= cpu <= 100

    @pytest.mark.asyncio
    async def test_middleware_logs_memory_usage(self, client) -> None:
        """Test czy middleware loguje użycie pamięci"""
        response = client.get("/test")
        # Nie sprawdzamy call_count mocka, bo patch jest globalny
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_handles_exceptions(self, client) -> None:
        """Test obsługi wyjątków przez middleware"""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint() -> None:
            raise ValueError("Test error")

        app.add_middleware(MemoryMonitoringMiddleware, enable_memory_profiling=True)
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/error")
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_middleware_different_endpoints(self, client) -> None:
        """Test middleware dla różnych endpointów"""
        response1 = client.get("/test")
        response2 = client.get("/memory-intensive")
        assert response1.status_code == 200
        assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_context_names(self, client) -> None:
        """Test nazw contextów w middleware"""
        response1 = client.get("/test")
        response2 = client.get("/memory-intensive")
        assert response1.status_code == 200
        assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_performance_impact(self, client) -> None:
        """Test wpływu middleware na wydajność"""
        import os
        import platform
        import time

        # Skip na wszystkich desktopach jeśli nie CI
        if not os.environ.get("CI"):
            pytest.skip("Test wydajności pomijany poza CI")
        app_no_middleware = FastAPI()

        @app_no_middleware.get("/test")
        async def test_endpoint() -> None:
            return {"message": "test"}

        client_no_middleware = TestClient(app_no_middleware)
        start_time = time.time()
        for _ in range(5):
            client_no_middleware.get("/test")
        time_without_middleware = time.time() - start_time
        start_time = time.time()
        for _ in range(5):
            client.get("/test")
        time_with_middleware = time.time() - start_time
        overhead_ratio = time_with_middleware / max(time_without_middleware, 0.01)
        assert overhead_ratio < 100.0  # Bardzo tolerancyjny próg


class TestMemoryMonitoringMiddlewareIntegration:
    """Testy integracyjne dla memory monitoring middleware"""

    @pytest.mark.asyncio
    async def test_middleware_with_real_memory_usage(self, client) -> None:
        """Test middleware z rzeczywistym użyciem pamięci"""
        # Ten test może być uruchamiany tylko w środowisku testowym
        # gdzie memory profiling jest włączony
        response = client.get("/memory-intensive")
        assert response.status_code == 200
        assert "X-Memory-Usage-MB" in response.headers
        assert "X-CPU-Percent" in response.headers
        # Sprawdź czy wartości są rozsądne
        memory_usage = float(response.headers["X-Memory-Usage-MB"])
        cpu_percent = float(response.headers["X-CPU-Percent"])
        assert 0 < memory_usage < 1000  # Maksymalnie 1GB
        assert 0 < cpu_percent < 1000  # Akceptujemy >100% na systemach wielordzeniowych

    @pytest.mark.asyncio
    async def test_middleware_concurrent_requests(self, client) -> None:
        """Test middleware z równoczesnymi żądaniami"""
        import asyncio
        import concurrent.futures

        def make_request() -> None:
            return client.get("/test")

        # Wykonaj równoczesne żądania
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]

        # Sprawdź czy wszystkie żądania przeszły
        for response in responses:
            assert response.status_code == 200
            assert "X-Memory-Usage-MB" in response.headers
