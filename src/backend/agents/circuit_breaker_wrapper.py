import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional, Type

import pybreaker

logger = logging.getLogger(__name__)


class AgentCircuitBreaker:
    """
    Wrapper dla Circuit Breaker dla asynchronicznych wywołań agentów.
    """

    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        reset_timeout: int = 30,
        exclude_exceptions: Optional[list[Type[Exception]]] = None,
    ) -> None:
        self.name = name
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            exclude=exclude_exceptions
            or [
                ValueError,
                TypeError,
            ],  # Typowe błędy biznesowe nie powinny otwierać obwodu
        )
        logger.info(
            f"Circuit Breaker '{name}' initialized with fail_max={fail_max}, reset_timeout={reset_timeout}"
        )

    async def run(
        self, func: Callable[..., Coroutine], *args: Any, **kwargs: Any
    ) -> None:
        """
        Wykonuje asynchroniczną funkcję, chroniąc ją przez Circuit Breaker.
        """
        try:
            # Pybreaker wymaga synchronicznego callable, więc używamy asyncio.to_thread
            result = await asyncio.to_thread(self._sync_wrapper, func, *args, **kwargs)
            return result
        except pybreaker.CircuitBreakerError as e:
            logger.error(
                f"Circuit Breaker '{self.name}' is OPEN. Preventing call to {func.__name__}. Error: {e}"
            )
            raise  # Przekaż błąd do wyższej warstwy obsługi fallbacków
        except Exception as e:
            # Inne nieoczekiwane błędy zostaną obsłużone przez pybreaker, jeśli nie są wykluczone
            logger.error(
                f"Error in Circuit Breaker protected call to {func.__name__}: {e}",
                exc_info=True,
            )
            raise

    def _sync_wrapper(
        self, func: Callable[..., Coroutine], *args: Any, **kwargs: Any
    ) -> None:
        """
        Synchroniczny wrapper dla asynchronicznej funkcji, używany przez pybreaker.
        """

        # Używamy pybreaker.CircuitBreaker jako dekoratora dla wewnętrznej funkcji
        @self.breaker
        def _execute_sync() -> None:
            # Musimy uruchomić asynchroniczną funkcję w istniejącym loopie lub nowym
            # Najlepiej użyć istniejącego loopa, ale to wymaga, by _sync_wrapper był wywoływany w kontekście loopa.
            # asyncio.to_thread odpala w nowym wątku, więc nowy loop jest ok.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(func(*args, **kwargs))
            finally:
                loop.close()

        return _execute_sync()

    def get_state(self) -> str:
        """Zwraca aktualny stan Circuit Breaker."""
        return str(self.breaker.current_state)

    def is_open(self) -> bool:
        """Sprawdza, czy obwód jest otwarty."""
        return self.breaker.current_state == pybreaker.STATE_OPEN
