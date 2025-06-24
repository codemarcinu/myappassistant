import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..error_types import ErrorSeverity
from ..interfaces import IAlertService


class AlertService(IAlertService):
    """Service for handling critical error alerts"""

    def __init__(
        self, name: str, alert_config: Optional[Dict[str, Any]] = None
    ) -> None:
        self.name = name
        self.alert_config = alert_config or {
            "enabled": True,
            "min_severity": ErrorSeverity.HIGH,
            "throttle_period": 3600,  # seconds
        }
        self.last_alerts: Dict[str, datetime] = {}

    def should_alert(self, error_message: str, severity: ErrorSeverity) -> bool:
        """Determine if an alert should be sent"""
        if not self.alert_config["enabled"]:
            return False

        severity_levels = {
            ErrorSeverity.LOW: 1,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.CRITICAL: 4,
        }

        if (
            severity_levels[severity]
            < severity_levels[self.alert_config["min_severity"]]
        ):
            return False

        error_key = f"{self.name}:{error_message[:50]}"
        now = datetime.now()

        if error_key in self.last_alerts:
            time_since_last = (now - self.last_alerts[error_key]).total_seconds()
            if time_since_last < self.alert_config["throttle_period"]:
                return False

        self.last_alerts[error_key] = now
        return True

    async def send_alert(
        self,
        message: str,
        severity: ErrorSeverity,
        error_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send alert notification"""
        if not self.should_alert(message, severity):
            return

        logging.warning(f"AGENT ALERT: {message} ({severity})")

        # In production would send email/Slack alerts here
        # Example implementation:
        # if self.alert_config.get("email_enabled"):
        #     await self._send_email_alert(subject, error_info)
        # if self.alert_config.get("slack_enabled"):
        #     await self._send_slack_alert(subject, error_info)
