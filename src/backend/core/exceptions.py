"""
Centralny system obsługi błędów dla FoodSave AI
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseCustomException(Exception):
    """Bazowa klasa dla wszystkich niestandardowych wyjątków"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "medium",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.severity = severity
        self.timestamp = self._get_timestamp()

        # Log the exception
        self._log_exception()

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

    def _log_exception(self) -> None:
        """Log the exception with appropriate level"""
        log_message = f"{self.__class__.__name__}: {self.message}"
        if self.error_code:
            log_message += f" (Code: {self.error_code})"
        if self.details:
            log_message += f" Details: {self.details}"

        if self.severity == "critical":
            logger.critical(log_message, exc_info=True)
        elif self.severity == "high":
            logger.error(log_message, exc_info=True)
        elif self.severity == "medium":
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class ValidationError(BaseCustomException):
    """Błędy walidacji danych wejściowych"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


class AIModelError(BaseCustomException):
    """Błędy związane z modelami AI"""

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if model_name:
            details["model_name"] = model_name
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code="AI_MODEL_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class DatabaseError(BaseCustomException):
    """Błędy bazy danych"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
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


class NetworkError(BaseCustomException):
    """Błędy sieciowe"""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
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


class FileProcessingError(BaseCustomException):
    """Błędy przetwarzania plików"""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if file_path:
            details["file_path"] = file_path
        if file_type:
            details["file_type"] = file_type

        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


class AgentError(BaseCustomException):
    """Błędy agentów"""

    def __init__(
        self,
        message: str,
        agent_type: Optional[str] = None,
        agent_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if agent_type:
            details["agent_type"] = agent_type
        if agent_name:
            details["agent_name"] = agent_name

        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


class ConfigurationError(BaseCustomException):
    """Błędy konfiguracji"""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs) -> None:
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class AuthenticationError(BaseCustomException):
    """Błędy uwierzytelniania"""

    def __init__(self, message: str, user_id: Optional[str] = None, **kwargs) -> None:
        details = kwargs.get("details", {})
        if user_id:
            details["user_id"] = user_id

        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class AuthorizationError(BaseCustomException):
    """Błędy autoryzacji"""

    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        required_permission: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if user_id:
            details["user_id"] = user_id
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            severity="high",
            **kwargs,
        )


class RateLimitError(BaseCustomException):
    """Błędy limitu żądań"""

    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs) -> None:
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


class CircuitBreakerError(BaseCustomException):
    """Błędy circuit breakera"""

    def __init__(self, message: str, circuit_name: Optional[str] = None, **kwargs) -> None:
        details = kwargs.get("details", {})
        if circuit_name:
            details["circuit_name"] = circuit_name

        super().__init__(
            message=message,
            error_code="CIRCUIT_BREAKER_ERROR",
            details=details,
            severity="medium",
            **kwargs,
        )


# Utility functions for exception handling
def handle_exceptions(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions_to_catch: Optional[tuple] = None,
    fallback_response: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Decorator do obsługi wyjątków z mechanizmem retry

    Args:
        max_retries: Maksymalna liczba prób
        retry_delay: Opóźnienie między próbami w sekundach
        exceptions_to_catch: Krotka wyjątków do przechwycenia
        fallback_response: Odpowiedź fallback w przypadku błędu
    """
    import asyncio
    import functools
    import time

    def decorator(func) -> None:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> None:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Sprawdź czy to wyjątek, który chcemy przechwycić
                    if exceptions_to_catch and not isinstance(e, exceptions_to_catch):
                        raise

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {retry_delay} seconds..."
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}"
                        )

            # Jeśli wszystkie próby się nie powiodły
            if fallback_response:
                return fallback_response

            # Rzuć ostatni wyjątek
            if last_exception is None:
                raise ValueError(
                    "handle_exceptions decorator used with max_retries < 0"
                )
            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> None:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Sprawdź czy to wyjątek, który chcemy przechwycić
                    if exceptions_to_catch and not isinstance(e, exceptions_to_catch):
                        raise

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {retry_delay} seconds..."
                        )
                        # MDC-FIXED: Zastąpienie time.sleep przez asyncio.run dla proper async handling
                        try:
                            asyncio.run(asyncio.sleep(retry_delay))
                        except RuntimeError:
                            # Jeśli już jest event loop, użyj time.sleep jako fallback
                            time.sleep(retry_delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}"
                        )

            # Jeśli wszystkie próby się nie powiodły
            if fallback_response:
                return fallback_response

            # Rzuć ostatni wyjątek
            if last_exception is None:
                raise ValueError(
                    "handle_exceptions decorator used with max_retries < 0"
                )
            raise last_exception

        # Zwróć odpowiedni wrapper w zależności od typu funkcji
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def convert_system_exception(exception: Exception) -> BaseCustomException:
    """
    Konwertuje systemowy wyjątek na niestandardowy

    Args:
        exception: Systemowy wyjątek

    Returns:
        Odpowiedni niestandardowy wyjątek
    """
    exception_type = type(exception)

    # Mapowanie typów wyjątków
    exception_mapping = {
        ValueError: ValidationError,
        TypeError: ValidationError,
        KeyError: ValidationError,
        IndexError: ValidationError,
        FileNotFoundError: FileProcessingError,
        PermissionError: FileProcessingError,
        ConnectionError: NetworkError,
        TimeoutError: NetworkError,
        OSError: FileProcessingError,
    }

    # Znajdź odpowiedni typ wyjątku
    custom_exception_type = exception_mapping.get(exception_type, BaseCustomException)

    # Utwórz niestandardowy wyjątek
    return custom_exception_type(
        message=str(exception), details={"original_exception": exception_type.__name__}
    )


def log_exception_with_context(
    exception: Exception, context: Optional[Dict[str, Any]] = None, level: str = "error"
) -> None:
    """
    Loguje wyjątek z dodatkowym kontekstem

    Args:
        exception: Wyjątek do zalogowania
        context: Dodatkowy kontekst
        level: Poziom logowania
    """
    context = context or {}

    log_message = f"Exception: {type(exception).__name__}: {str(exception)}"
    if context:
        log_message += f" Context: {context}"

    if level == "critical":
        logger.critical(log_message, exc_info=True)
    elif level == "error":
        logger.error(log_message, exc_info=True)
    elif level == "warning":
        logger.warning(log_message)
    else:
        logger.info(log_message)
