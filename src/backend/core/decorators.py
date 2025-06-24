import asyncio
import functools
import logging
import time
from typing import Any, Callable, TypeVar

from backend.core.exceptions import (ConfigurationError, DatabaseError,
                                     ExternalAPIError, FoodSaveError,
                                     ProcessingError)

logger = logging.getLogger(__name__)
T = TypeVar("T")


def handle_exceptions(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_exceptions: tuple = (DatabaseError, ExternalAPIError),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to handle exceptions and implement retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        retry_exceptions: Tuple of exception types to retry on
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)  # type: ignore[misc]
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after error: {str(e)}"
                        )
                        await asyncio.sleep(retry_delay)
                        continue
                    raise
                except Exception as e:
                    last_exception = e
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                    raise convert_to_custom_exception(e) from e

            raise last_exception if last_exception else RuntimeError("Unexpected error")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after error: {str(e)}"
                        )
                        # MDC-FIXED: Zastąpienie time.sleep przez asyncio.run dla proper async handling
                        try:
                            asyncio.run(asyncio.sleep(retry_delay))
                        except RuntimeError:
                            # Jeśli już jest event loop, użyj time.sleep jako fallback
                            time.sleep(retry_delay)
                        continue
                    raise
                except Exception as e:
                    last_exception = e
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                    raise convert_to_custom_exception(e) from e

            raise last_exception if last_exception else RuntimeError("Unexpected error")

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper  # type: ignore[return-value]

    return decorator


def convert_to_custom_exception(exc: Exception) -> FoodSaveError:
    """Convert system exceptions to custom exceptions"""
    if isinstance(exc, FoodSaveError):
        return exc

    exc_str = str(exc)
    if "database" in exc_str.lower() or "sql" in exc_str.lower():
        return DatabaseError(f"Database error: {exc_str}")
    elif "network" in exc_str.lower() or "connection" in exc_str.lower():
        return ExternalAPIError(f"Network error: {exc_str}")
    elif "file" in exc_str.lower() or "io" in exc_str.lower():
        return ProcessingError(f"File processing error: {exc_str}")
    elif "model" in exc_str.lower() or "ai" in exc_str.lower():
        return ProcessingError(f"AI model error: {exc_str}")

    return ProcessingError(f"Unexpected error: {exc_str}")
