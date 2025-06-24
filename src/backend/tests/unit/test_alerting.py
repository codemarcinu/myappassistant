from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Tests dla Alerting System
Zgodnie z regułami MDC dla testowania i monitoringu
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from backend.core.alerting import (Alert, AlertManager, AlertRule,
                                   AlertSeverity, AlertStatus,
                                   record_system_metrics)


class TestAlerting:
    """Testy dla alerting system"""

    @pytest.fixture
    def alert_manager(self) -> None:
        """Fixture dla AlertManager"""
        return AlertManager()

    @pytest.fixture
    def sample_rule(self) -> None:
        """Fixture dla sample alert rule"""
        return AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            threshold=10.0,
            operator=">",
            severity=AlertSeverity.HIGH,
            duration=60,
        )

    def test_alert_manager_initialization(self, alert_manager) -> None:
        """Test AlertManager initialization"""
        assert len(alert_manager.rules) > 0  # Should have default rules
        assert len(alert_manager.active_alerts) == 0
        assert len(alert_manager.alert_history) == 0
        assert len(alert_manager.handlers) > 0  # Should have default handlers

    def test_add_remove_rule(self, alert_manager, sample_rule) -> None:
        """Test adding and removing alert rules"""
        # Add rule
        alert_manager.add_rule(sample_rule)
        assert sample_rule.name in alert_manager.rules

        # Remove rule
        alert_manager.remove_rule(sample_rule.name)
        assert sample_rule.name not in alert_manager.rules

    def test_record_metric(self, alert_manager) -> None:
        """Test recording metrics"""
        alert_manager.record_metric("test_metric", 15.0)
        assert "test_metric" in alert_manager.metric_values
        assert len(alert_manager.metric_values["test_metric"]) == 1
        assert alert_manager.metric_values["test_metric"][0][0] == 15.0

    def test_metric_value_cleanup(self, alert_manager) -> None:
        """Test that old metric values are cleaned up"""
        # Add more than 1000 values
        for i in range(1100):
            alert_manager.record_metric("test_metric", float(i))

        # Should keep only last 1000
        assert len(alert_manager.metric_values["test_metric"]) == 1000
        assert alert_manager.metric_values["test_metric"][-1][0] == 1099.0

    def test_evaluate_rule_threshold_exceeded(self, alert_manager, sample_rule) -> None:
        """Test rule evaluation when threshold is exceeded"""
        alert_manager.add_rule(sample_rule)

        # Record metric above threshold
        alert_manager.record_metric("test_metric", 15.0)

        # Evaluate rule
        alert = alert_manager._evaluate_rule(sample_rule)

        assert alert is not None
        assert alert.rule.name == sample_rule.name
        assert alert.value == 15.0
        assert alert.status == AlertStatus.ACTIVE

    def test_evaluate_rule_threshold_not_exceeded(
        self, alert_manager, sample_rule
    ) -> None:
        """Test rule evaluation when threshold is not exceeded"""
        alert_manager.add_rule(sample_rule)

        # Record metric below threshold
        alert_manager.record_metric("test_metric", 5.0)

        # Evaluate rule
        alert = alert_manager._evaluate_rule(sample_rule)

        assert alert is None

    def test_evaluate_rule_with_duration_window(
        self, alert_manager, sample_rule
    ) -> None:
        """Test rule evaluation with duration window"""
        alert_manager.add_rule(sample_rule)

        # Record old metric (outside duration window)
        old_time = datetime.now() - timedelta(seconds=120)
        alert_manager.metric_values["test_metric"] = [(15.0, old_time)]

        # Evaluate rule - should not trigger because metric is too old
        alert = alert_manager._evaluate_rule(sample_rule)
        assert alert is None

    @pytest.mark.asyncio
    async def test_check_alerts(self, alert_manager, sample_rule) -> None:
        """Test checking all alerts"""
        alert_manager.add_rule(sample_rule)
        alert_manager.record_metric("test_metric", 15.0)

        # Check alerts
        new_alerts = await alert_manager.check_alerts()

        assert len(new_alerts) == 1
        assert new_alerts[0].rule.name == sample_rule.name
        assert len(alert_manager.active_alerts) == 1
        assert len(alert_manager.alert_history) == 1

    def test_acknowledge_alert(self, alert_manager, sample_rule) -> None:
        """Test acknowledging an alert"""
        alert_manager.add_rule(sample_rule)
        alert_manager.record_metric("test_metric", 15.0)

        # Create alert
        alert = alert_manager._evaluate_rule(sample_rule)
        alert_manager.active_alerts[sample_rule.name] = alert

        # Acknowledge alert
        alert_manager.acknowledge_alert(sample_rule.name, "test_user")

        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == "test_user"

    def test_resolve_alert(self, alert_manager, sample_rule) -> None:
        """Test resolving an alert"""
        alert_manager.add_rule(sample_rule)
        alert_manager.record_metric("test_metric", 15.0)

        # Create alert
        alert = alert_manager._evaluate_rule(sample_rule)
        alert_manager.active_alerts[sample_rule.name] = alert

        # Resolve alert
        alert_manager.resolve_alert(sample_rule.name)

        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert sample_rule.name not in alert_manager.active_alerts

    def test_get_active_alerts(self, alert_manager, sample_rule) -> None:
        """Test getting active alerts"""
        alert_manager.add_rule(sample_rule)
        alert_manager.record_metric("test_metric", 15.0)

        # Create alert
        alert = alert_manager._evaluate_rule(sample_rule)
        alert_manager.active_alerts[sample_rule.name] = alert

        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].rule.name == sample_rule.name

    def test_get_alert_history(self, alert_manager, sample_rule) -> None:
        """Test getting alert history"""
        alert_manager.add_rule(sample_rule)
        alert_manager.record_metric("test_metric", 15.0)

        # Create alert
        alert = alert_manager._evaluate_rule(sample_rule)
        alert_manager.alert_history.append(alert)

        # Get history for last 24 hours
        history = alert_manager.get_alert_history(24)
        assert len(history) == 1
        assert history[0].rule.name == sample_rule.name

    def test_get_alert_stats(self, alert_manager, sample_rule) -> None:
        """Test getting alert statistics"""
        alert_manager.add_rule(sample_rule)
        alert_manager.record_metric("test_metric", 15.0)

        # Create alert
        alert = alert_manager._evaluate_rule(sample_rule)
        alert_manager.active_alerts[sample_rule.name] = alert
        alert_manager.alert_history.append(alert)

        stats = alert_manager.get_alert_stats()

        assert stats["total_alerts"] == 1
        assert stats["active_alerts"] == 1
        assert "severity_distribution" in stats
        assert "last_check" in stats

    def test_alert_cooldown(self, alert_manager, sample_rule) -> None:
        """Test alert cooldown mechanism"""
        sample_rule.cooldown = 300  # 5 minutes
        alert_manager.add_rule(sample_rule)

        # Record metric and create first alert
        alert_manager.record_metric("test_metric", 15.0)
        alert1 = alert_manager._evaluate_rule(sample_rule)
        alert_manager.active_alerts[sample_rule.name] = alert1

        # Try to create second alert immediately - should be blocked by cooldown
        alert2 = alert_manager._evaluate_rule(sample_rule)
        assert alert2 is None

    def test_record_system_metrics(self) -> None:
        """Test recording system metrics"""
        with patch("psutil.Process") as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024
            mock_process.return_value.memory_percent.return_value = 50.0
            mock_process.return_value.cpu_percent.return_value = 25.0

            with patch("psutil.disk_usage") as mock_disk:
                mock_disk.return_value.used = 1024 * 1024 * 1024
                mock_disk.return_value.total = 1024 * 1024 * 1024 * 10

                # Should not raise exception
                record_system_metrics()

    def test_alert_rule_operators(self, alert_manager) -> None:
        """Test different alert rule operators"""
        operators = [">", ">=", "<", "<=", "=="]

        for operator in operators:
            rule = AlertRule(
                name=f"test_rule_{operator}",
                description=f"Test rule with {operator}",
                metric_name="test_metric",
                threshold=10.0,
                operator=operator,
                severity=AlertSeverity.MEDIUM,
            )

            alert_manager.add_rule(rule)
            alert_manager.record_metric("test_metric", 15.0)

            alert = alert_manager._evaluate_rule(rule)

            # Check if alert is created based on operator
            if operator in [">", ">="]:
                assert alert is not None
            elif operator in ["<", "<="]:
                assert alert is None
            elif operator == "==":
                assert alert is None  # 15 != 10
