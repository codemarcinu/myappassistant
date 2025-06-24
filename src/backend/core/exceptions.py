"""
✅ REQUIRED: Custom exception hierarchy for FoodSave AI application
This module provides a comprehensive exception system with proper error context and logging.
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FoodSaveError(Exception):
    """✅ REQUIRED: Base exception for FoodSave application"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "medium",
        **kwargs: Any,
    ) -> None:
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.severity = severity
        self.timestamp = datetime.now()
        self.context = kwargs

        # ✅ ALWAYS: Proper error context and logging
        logger.error(
            f"FoodSave error: {message}",
            extra={
                "error_code": self.error_code,
                "severity": self.severity,
                "details": self.details,
                "context": self.context,
                "timestamp": self.timestamp.isoformat(),
            },
        )

        super().__init__(self.message)

    @property
    def status_code(self) -> int:
        """Return appropriate HTTP status code based on error type"""
        if isinstance(self, ValidationError):
            return 400
        elif isinstance(self, AuthenticationError):
            return 401
        elif isinstance(self, DatabaseError):
            return 500
        elif isinstance(self, ExternalAPIError):
            return 502
        elif isinstance(self, RateLimitError):
            return 429
        elif isinstance(self, HealthCheckError):
            return 503
        else:
            return 500

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


class ProcessingError(FoodSaveError):
    """✅ REQUIRED: Raised when food processing fails"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        food_item_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        if food_item_id:
            details["food_item_id"] = food_item_id

        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class AgentError(FoodSaveError):
    """✅ REQUIRED: Raised when agent operations fail"""

    def __init__(
        self,
        message: str,
        agent_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if agent_type:
            details["agent_type"] = agent_type
        if agent_id:
            details["agent_id"] = agent_id

        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class DatabaseError(FoodSaveError):
    """✅ REQUIRED: Database-related errors"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class ValidationError(FoodSaveError):
    """Input validation errors"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


class AuthenticationError(FoodSaveError):
    """Authentication and authorization errors"""

    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if user_id:
            details["user_id"] = user_id
        if session_id:
            details["session_id"] = session_id

        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class ExternalAPIError(FoodSaveError):
    """External API integration errors"""

    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if api_name:
            details["api_name"] = api_name
        if endpoint:
            details["endpoint"] = endpoint
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


class ConfigurationError(FoodSaveError):
    """Configuration and setup errors"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class RateLimitError(FoodSaveError):
    """Rate limiting errors"""

    def __init__(
        self,
        message: str,
        limit_type: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if limit_type:
            details["limit_type"] = limit_type
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


class HealthCheckError(FoodSaveError):
    """Health check failures"""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        check_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if service:
            details["service"] = service
        if check_type:
            details["check_type"] = check_type

        super().__init__(
            message=message,
            error_code="HEALTH_CHECK_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class NetworkError(FoodSaveError):
    """Network and connectivity errors"""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


# Error handling utilities
def handle_exception_with_context(
    exception: Exception, context: Dict[str, Any], operation: str, **kwargs: Any
) -> FoodSaveError:
    """✅ ALWAYS: Proper error context and logging"""
    # Determine the appropriate exception type
    if isinstance(exception, FoodSaveError):
        exception.context.update(context)
        return exception

    # Create a copy of context without operation to avoid conflicts
    context_copy = context.copy()
    context_copy.pop("operation", None)
    error_message = str(exception).lower()
    if "database" in error_message or "sql" in error_message:
        exc = DatabaseError(
            message=str(exception),
            operation=operation,
            details={"original_error": type(exception).__name__},
            **context_copy,
            **kwargs,
        )
    elif "validation" in error_message:
        exc = ValidationError(
            message=str(exception),
            details={"original_error": type(exception).__name__},
            **context_copy,
            **kwargs,
        )
    elif "authentication" in error_message or "auth" in error_message:
        exc = AuthenticationError(
            message=str(exception),
            details={"original_error": type(exception).__name__},
            **context_copy,
            **kwargs,
        )
    else:
        exc = ProcessingError(
            message=str(exception),
            operation=operation,
            details={
                "original_error": type(exception).__name__,
                "stack_trace": traceback.format_exc(),
            },
            **context_copy,
            **kwargs,
        )
    # Ensure the full context (including 'operation') is present
    exc.context.update(context)
    return exc


def log_error_with_context(
    error: Exception, context: Dict[str, Any], operation: str, **kwargs: Any
) -> None:
    """Log error with full context for debugging"""

    logger.error(
        f"Error in {operation}: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "operation": operation,
            "context": context,
            "stack_trace": traceback.format_exc(),
            **kwargs,
        },
    )


# Error response utilities
def create_error_response(
    error: FoodSaveError, include_details: bool = False
) -> Dict[str, Any]:
    """Create standardized error response"""

    response = {
        "success": False,
        "error_code": error.error_code,
        "message": error.message,
        "timestamp": error.timestamp.isoformat(),
        "severity": error.severity,
    }

    if include_details:
        response["details"] = error.details
        response["context"] = error.context

    return response


def convert_system_exception(exception: Exception) -> FoodSaveError:
    """Convert system exceptions to FoodSave exceptions with proper context"""

    # If it's already a FoodSave error, return it
    if isinstance(exception, FoodSaveError):
        return exception

    # Map common system exceptions to FoodSave errors
    if isinstance(exception, ValueError):
        return ValidationError(
            message=str(exception), details={"original_error": "ValueError"}
        )
    elif isinstance(exception, KeyError):
        return ValidationError(
            message=f"Missing required field: {str(exception)}",
            details={"original_error": "KeyError"},
        )
    elif isinstance(exception, TypeError):
        return ValidationError(
            message=str(exception), details={"original_error": "TypeError"}
        )
    elif isinstance(exception, AttributeError):
        return ProcessingError(
            message=str(exception), details={"original_error": "AttributeError"}
        )
    else:
        # Generic processing error for unknown exceptions
        return ProcessingError(
            message=str(exception),
            details={
                "original_error": type(exception).__name__,
                "stack_trace": traceback.format_exc(),
            },
        )
