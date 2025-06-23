from typing import Any, Dict, Optional

from fastapi import status

from backend.core.exceptions import FoodSaveError


# Lokalne definicje kodów błędów zamiast importu z api.v2.exceptions
class APIErrorCodes:
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"


class OrchestratorError(FoodSaveError):
    """Custom error for orchestrator-related issues"""

    pass


class AgentProcessingError(OrchestratorError):
    """Error during agent processing."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=f"Agent processing error: {message}", details=details)


class ServiceUnavailableError(OrchestratorError):
    """Required service is unavailable."""

    def __init__(
        self, service_name: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=f"Service {service_name} is unavailable",
            error_code=APIErrorCodes.SERVICE_UNAVAILABLE,
            details=details,
            severity="high",
        )


class IntentRecognitionError(OrchestratorError):
    """Error during intent recognition."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=f"Intent recognition error: {message}", details=details
        )


class MemoryManagerError(OrchestratorError):
    """Error related to memory management."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=f"Memory manager error: {message}", details=details)


class ProfileManagerError(OrchestratorError):
    """Error related to user profile management."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=f"Profile manager error: {message}", details=details)
