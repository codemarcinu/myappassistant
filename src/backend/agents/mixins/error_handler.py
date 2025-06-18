import logging
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, Optional

from ..error_types import ErrorSeverity


class ErrorHandler:
    """Handler for error processing and recovery with alerting capabilities"""

    def __init__(self, name: str, alert_config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.alert_config = alert_config or {
            "enabled": True,
            "min_severity": ErrorSeverity.HIGH,
            "throttle_period": 3600,
        }
        self.last_alerts: Dict[str, datetime] = {}

    async def execute_with_fallback(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        fallback_handler: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None,
        error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        **kwargs,
    ) -> tuple[Any, bool, Optional[str], float]:
        """
        Execute a function with automatic fallback and error handling
        Returns tuple of (result, used_fallback, error_message, processing_time)
        """
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            return result, False, None, time.time() - start_time

        except Exception as e:
            error_info = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat(),
            }
            logging.error(f"Error in {self.name}.{func.__name__}: {str(e)}")

            if self._should_alert(str(e), error_severity):
                await self._send_alert(
                    f"Error in {self.name}.{func.__name__}", error_info, error_severity
                )

            if fallback_handler:
                try:
                    logging.info(f"Attempting fallback for {func.__name__}")
                    result = await fallback_handler(*args, error=e, **kwargs)
                    return result, True, str(e), time.time() - start_time
                except Exception as fallback_error:
                    logging.error(f"Fallback also failed: {str(fallback_error)}")
                    error_info["fallback_error"] = str(fallback_error)

            return None, True, str(e), time.time() - start_time

    def _should_alert(self, error_message: str, severity: ErrorSeverity) -> bool:
        """Determine if an alert should be sent based on severity and throttling"""
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

    async def _send_alert(
        self, subject: str, error_info: Dict[str, Any], severity: ErrorSeverity
    ) -> None:
        """Send alert notification via configured channels"""
        if not self.alert_config["enabled"]:
            return

        logging.warning(f"AGENT ALERT: {subject} ({severity})")
        # In production would send email/Slack alerts here
