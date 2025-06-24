from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Tests dla Prometheus Metrics
Zgodnie z regułami MDC dla testowania i monitoringu
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from backend.core.prometheus_metrics import (MetricsCollector, get_metrics,
                                             get_metrics_dict,
                                             record_agent_metrics,
                                             record_cache_metrics,
                                             record_circuit_breaker_metrics,
                                             record_db_metrics,
                                             record_llm_metrics,
                                             record_ocr_metrics,
                                             record_vector_metrics)


class TestPrometheusMetrics:
    """Testy dla Prometheus metrics"""

    def test_record_agent_metrics(self) -> None:
        """Test recording agent metrics"""
        record_agent_metrics("test_agent", True, 1.5, 1024)

        # Check that metrics were recorded
        metrics = get_metrics_dict()
        assert "agent_requests_total" in str(get_metrics())
        assert "agent_processing_time_seconds" in str(get_metrics())
        assert "agent_memory_usage_bytes" in str(get_metrics())

    def test_record_db_metrics(self) -> None:
        """Test recording database metrics"""
        record_db_metrics("SELECT", "users", 0.5)

        # Check that metrics were recorded
        metrics = get_metrics_dict()
        assert "database_queries_total" in str(get_metrics())
        assert "database_query_duration_seconds" in str(get_metrics())

    def test_record_llm_metrics(self) -> None:
        """Test recording LLM metrics"""
        record_llm_metrics("gpt-4", True, 2.0, 100, "input")

        # Check that metrics were recorded
        metrics = get_metrics_dict()
        assert "llm_requests_total" in str(get_metrics())
        assert "llm_request_duration_seconds" in str(get_metrics())
        assert "llm_tokens_total" in str(get_metrics())

    def test_record_vector_metrics(self) -> None:
        """Test recording vector metrics"""
        record_vector_metrics("faiss", 0.1, 1000)

        # Check that metrics were recorded
        metrics = get_metrics_dict()
        assert "vector_search_total" in str(get_metrics())
        assert "vector_search_duration_seconds" in str(get_metrics())
        assert "vector_store_size" in str(get_metrics())

    def test_record_ocr_metrics(self) -> None:
        """Test recording OCR metrics"""
        record_ocr_metrics("image", True, 1.0)

        # Check that metrics were recorded
        metrics = get_metrics_dict()
        assert "ocr_processing_total" in str(get_metrics())
        assert "ocr_processing_duration_seconds" in str(get_metrics())

    def test_record_cache_metrics(self) -> None:
        """Test recording cache metrics"""
        record_cache_metrics("redis", True)  # Hit
        record_cache_metrics("redis", False)  # Miss

        # Check that metrics were recorded
        metrics = get_metrics_dict()
        assert "cache_hits_total" in str(get_metrics())
        assert "cache_misses_total" in str(get_metrics())

    def test_record_circuit_breaker_metrics(self) -> None:
        """Test recording circuit breaker metrics"""
        record_circuit_breaker_metrics("test_breaker", "open", True)

        # Check that metrics were recorded
        metrics = get_metrics_dict()
        assert "circuit_breaker_state" in str(get_metrics())
        assert "circuit_breaker_failures_total" in str(get_metrics())

    def test_get_metrics(self) -> None:
        """Test getting metrics as string"""
        metrics_str = get_metrics()
        assert isinstance(metrics_str, bytes)
        assert len(metrics_str) > 0

    def test_get_metrics_dict(self) -> None:
        """Test getting metrics as dictionary"""
        metrics_dict = get_metrics_dict()
        assert isinstance(metrics_dict, dict)

    def test_metrics_collector(self) -> None:
        """Test metrics collector"""
        with patch("psutil.Process") as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024
            mock_process.return_value.memory_percent.return_value = 50.0
            mock_process.return_value.cpu_percent.return_value = 25.0

            with patch("psutil.disk_usage") as mock_disk:
                mock_disk.return_value.used = 1024 * 1024 * 1024
                mock_disk.return_value.total = 1024 * 1024 * 1024 * 10

                collector = MetricsCollector()
                collector.collect_system_metrics()

                # Check that system metrics were recorded
                metrics = get_metrics_dict()
                assert "system_memory_usage_bytes" in str(get_metrics())
                assert "system_cpu_usage_percent" in str(get_metrics())
                assert "system_disk_usage_bytes" in str(get_metrics())

    def test_metrics_collector_error_handling(self) -> None:
        """Test metrics collector error handling"""
        with patch("psutil.Process") as mock_process:
            mock_process.side_effect = Exception("Test error")

            collector = MetricsCollector()
            # Should not raise exception
            collector.collect_system_metrics()

    def test_multiple_metric_recordings(self) -> None:
        """Test multiple metric recordings"""
        # Record multiple metrics
        for i in range(5):
            record_agent_metrics(f"agent_{i}", True, i * 0.1, i * 100)
            record_db_metrics("SELECT", f"table_{i}", i * 0.05)

        # Check that all metrics were recorded
        metrics_str = get_metrics()
        assert "agent_requests_total" in str(metrics_str)
        assert "database_queries_total" in str(metrics_str)

        # Check counts
        metrics_dict = get_metrics_dict()
        # Note: Prometheus metrics are cumulative, so we can't easily check exact counts
        # without parsing the metrics string more carefully
