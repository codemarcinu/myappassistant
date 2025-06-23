"""
Alerting System dla Critical Thresholds
Zgodnie z regułami MDC dla monitoringu i observability
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    description: str
    metric_name: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    severity: AlertSeverity
    duration: int = 60  # seconds to trigger
    cooldown: int = 300  # seconds before re-triggering


@dataclass
class Alert:
    """Alert instance"""

    id: str
    rule: AlertRule
    value: float
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    message: str = ""


class AlertManager:
    """Manager dla alertów i monitoring thresholds"""

    def __init__(self) -> None:
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.handlers: List[Callable[[Alert], None]] = []
        self.metric_values: Dict[str, List[tuple]] = {}  # (value, timestamp)
        self.last_check = datetime.now()

        # Default alert rules
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="high_memory_usage",
                description="Memory usage above 80%",
                metric_name="system_memory_usage_bytes",
                threshold=0.8,
                operator=">",
                severity=AlertSeverity.HIGH,
                duration=30,
            ),
            AlertRule(
                name="high_cpu_usage",
                description="CPU usage above 90%",
                metric_name="system_cpu_usage_percent",
                threshold=90.0,
                operator=">",
                severity=AlertSeverity.MEDIUM,
                duration=60,
            ),
            AlertRule(
                name="database_connection_errors",
                description="Database connection errors",
                metric_name="database_connection_errors_total",
                threshold=5.0,
                operator=">",
                severity=AlertSeverity.CRITICAL,
                duration=10,
            ),
            AlertRule(
                name="high_error_rate",
                description="Error rate above 10%",
                metric_name="http_requests_total",
                threshold=0.1,
                operator=">",
                severity=AlertSeverity.HIGH,
                duration=30,
            ),
            AlertRule(
                name="slow_response_time",
                description="Average response time above 2 seconds",
                metric_name="http_request_duration_seconds",
                threshold=2.0,
                operator=">",
                severity=AlertSeverity.MEDIUM,
                duration=60,
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove alert rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
            return True
        return False

    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add alert handler"""
        self.handlers.append(handler)

    def record_metric(self, metric_name: str, value: float) -> None:
        """Record metric value"""
        if metric_name not in self.metric_values:
            self.metric_values[metric_name] = []

        self.metric_values[metric_name].append((value, datetime.now()))

        # Keep only last 1000 values
        if len(self.metric_values[metric_name]) > 1000:
            self.metric_values[metric_name] = self.metric_values[metric_name][-1000:]

    def _evaluate_rule(self, rule: AlertRule) -> Optional[Alert]:
        """Evaluate single alert rule"""
        if rule.metric_name not in self.metric_values:
            return None

        # Get recent values within duration window
        cutoff_time = datetime.now() - timedelta(seconds=rule.duration)
        recent_values = [
            value
            for value, timestamp in self.metric_values[rule.metric_name]
            if timestamp >= cutoff_time
        ]

        if not recent_values:
            return None

        # Calculate metric based on rule
        if rule.metric_name.startswith("http_requests_total"):
            # Special handling for error rate calculation
            total_requests = sum(recent_values)
            error_requests = sum(1 for v in recent_values if v > 0)  # Simplified
            if total_requests > 0:
                error_rate = error_requests / total_requests
                current_value = error_rate
            else:
                return None
        elif rule.metric_name.startswith("http_request_duration_seconds"):
            # Average response time
            current_value = sum(recent_values) / len(recent_values)
        else:
            # Use latest value
            current_value = recent_values[-1]

        # Check if threshold is exceeded
        threshold_exceeded = False
        if rule.operator == ">":
            threshold_exceeded = current_value > rule.threshold
        elif rule.operator == ">=":
            threshold_exceeded = current_value >= rule.threshold
        elif rule.operator == "<":
            threshold_exceeded = current_value < rule.threshold
        elif rule.operator == "<=":
            threshold_exceeded = current_value <= rule.threshold
        elif rule.operator == "==":
            threshold_exceeded = current_value == rule.threshold

        if threshold_exceeded:
            # Check if alert is already active
            alert_id = f"{rule.name}_{int(time.time())}"

            # Check cooldown
            if rule.name in self.active_alerts:
                last_alert = self.active_alerts[rule.name]
                if datetime.now() - last_alert.timestamp < timedelta(
                    seconds=rule.cooldown
                ):
                    return None

            # Create new alert
            alert = Alert(
                id=alert_id,
                rule=rule,
                value=current_value,
                timestamp=datetime.now(),
                message=f"{rule.description}: {current_value} {rule.operator} {rule.threshold}",
            )

            return alert

        return None

    async def check_alerts(self) -> None:
        """Check all alert rules"""
        new_alerts = []

        for rule in self.rules.values():
            alert = self._evaluate_rule(rule)
            if alert:
                new_alerts.append(alert)
                self.active_alerts[rule.name] = alert
                self.alert_history.append(alert)

                # Trigger handlers
                for handler in self.handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(alert)
                        else:
                            handler(alert)
                    except Exception as e:
                        logger.error(f"Error in alert handler: {e}")

        # Log new alerts
        for alert in new_alerts:
            logger.warning(
                f"Alert triggered: {alert.rule.name}",
                severity=alert.rule.severity.value,
                value=alert.value,
                threshold=alert.rule.threshold,
                message=alert.message,
            )

        return new_alerts

    def acknowledge_alert(self, rule_name: str, user: str) -> bool:
        """Acknowledge alert"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user
            logger.info(f"Alert acknowledged: {rule_name} by {user}")
            return True
        return False

    def resolve_alert(self, rule_name: str) -> bool:
        """Resolve alert"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            del self.active_alerts[rule_name]
            logger.info(f"Alert resolved: {rule_name}")
            return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)

        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len(
                [
                    alert
                    for alert in self.active_alerts.values()
                    if alert.rule.severity == severity
                ]
            )

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "severity_distribution": severity_counts,
            "last_check": self.last_check.isoformat(),
        }


# Global alert manager instance
alert_manager = AlertManager()


# Default alert handlers
def log_alert_handler(alert: Alert) -> None:
    """Default handler that logs alerts"""
    logger.error(
        f"ALERT: {alert.rule.severity.value.upper()} - {alert.rule.name}",
        value=alert.value,
        threshold=alert.rule.threshold,
        message=alert.message,
    )


def console_alert_handler(alert: Alert) -> None:
    """Handler that prints to console"""
    print(f"\n🚨 ALERT: {alert.rule.severity.value.upper()}")
    print(f"Rule: {alert.rule.name}")
    print(f"Value: {alert.value}")
    print(f"Threshold: {alert.rule.threshold}")
    print(f"Message: {alert.message}")
    print(f"Time: {alert.timestamp}\n")


# Register default handlers
alert_manager.add_handler(log_alert_handler)
alert_manager.add_handler(console_alert_handler)


# Background task dla alert checking
async def alert_checker_task() -> None:
    """Background task to check alerts periodically"""
    while True:
        try:
            await alert_manager.check_alerts()
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in alert checker: {e}")
            await asyncio.sleep(60)  # Wait longer on error


# Utility functions
def record_system_metrics() -> None:
    """Record system metrics for alerting"""
    import psutil

    process = psutil.Process()

    # Memory usage
    memory_percent = process.memory_percent()
    alert_manager.record_metric("system_memory_usage_bytes", memory_percent / 100.0)

    # CPU usage
    cpu_percent = process.cpu_percent()
    alert_manager.record_metric("system_cpu_usage_percent", cpu_percent)

    # Disk usage
    disk_usage = psutil.disk_usage("/")
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    alert_manager.record_metric("system_disk_usage_percent", disk_percent)


def start_alert_checker() -> None:
    """Start background alert checker task"""
    asyncio.create_task(alert_checker_task())
    logger.info("Alert checker task started")
