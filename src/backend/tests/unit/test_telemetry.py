from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Tests dla OpenTelemetry Integration
Zgodnie z regułami MDC dla testowania i monitoringu
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from backend.core.telemetry import (SpanContext, create_span, get_tracer,
                                    setup_telemetry, traced_async_function,
                                    traced_function)


class TestTelemetry:
    """Testy dla OpenTelemetry integration"""

    def test_setup_telemetry(self) -> None:
        """Test setup telemetry"""
        with patch("backend.core.telemetry.settings") as mock_settings:
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            # Should not fail in test environment
            setup_telemetry(enable_jaeger=False, enable_prometheus=False)
            assert get_tracer() is not None

    def test_create_span(self) -> None:
        """Test creating spans"""
        with patch("backend.core.telemetry.settings") as mock_settings:
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            setup_telemetry(enable_jaeger=False, enable_prometheus=False)

            span = create_span("test_span", {"test": "value"})
            assert span is not None
            assert span.name == "test_span"

    def test_span_context(self) -> None:
        """Test span context manager"""
        with patch("backend.core.telemetry.settings") as mock_settings:
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            setup_telemetry(enable_jaeger=False, enable_prometheus=False)

            with SpanContext("test_context", {"test": "value"}) as span:
                assert span is not None
                assert span.name == "test_context"

    def test_traced_function_decorator(self) -> None:
        """Test traced function decorator"""
        with patch("backend.core.telemetry.settings") as mock_settings:
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            setup_telemetry(enable_jaeger=False, enable_prometheus=False)

            @traced_function("test_function")
            def test_func() -> None:
                return "test"

            result = test_func()
            assert result == "test"

    @pytest.mark.asyncio
    async def test_traced_async_function_decorator(self) -> None:
        """Test traced async function decorator"""
        with patch("backend.core.telemetry.settings") as mock_settings:
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            setup_telemetry(enable_jaeger=False, enable_prometheus=False)

            @traced_async_function("test_async_function")
            async def test_async_func() -> None:
                await asyncio.sleep(0.01)
                return "test_async"

            result = await test_async_func()
            assert result == "test_async"

    def test_span_context_with_exception(self) -> None:
        """Test span context with exception handling"""
        with patch("backend.core.telemetry.settings") as mock_settings:
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            setup_telemetry(enable_jaeger=False, enable_prometheus=False)

            with pytest.raises(ValueError):
                with SpanContext("test_exception", {"test": "value"}) as span:
                    assert span is not None
                    raise ValueError("Test exception")

    def test_get_tracer_singleton(self) -> None:
        """Test that get_tracer returns singleton"""
        with patch("backend.core.telemetry.settings") as mock_settings:
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            setup_telemetry(enable_jaeger=False, enable_prometheus=False)

            tracer1 = get_tracer()
            tracer2 = get_tracer()
            assert tracer1 is tracer2
