"""
Async Patterns Implementation
Zgodnie z regułami MDC dla FastAPI Async Optimization
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info(
                        f"Circuit {self.config.name} transitioning to HALF_OPEN"
                    )
                else:
                    raise Exception(f"Circuit {self.config.name} is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)

            await self._on_success()
            return result

        except self.config.expected_exception:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit {self.config.name} is now CLOSED")

    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.config.name} is now OPEN")


class BackpressureManager:
    """Backpressure mechanism for high-load scenarios"""

    def __init__(self, max_concurrent: int = 100, max_queue_size: int = 1000):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.active_tasks = 0

    @asynccontextmanager
    async def acquire_slot(self):
        """Acquire a processing slot with backpressure"""
        try:
            await self.semaphore.acquire()
            self.active_tasks += 1
            yield
        finally:
            self.semaphore.release()
            self.active_tasks -= 1

    async def enqueue_task(self, task: Callable, *args, **kwargs):
        """Enqueue task with backpressure protection"""
        try:
            await self.queue.put((task, args, kwargs))
        except asyncio.QueueFull:
            logger.warning("Task queue is full, dropping task")
            raise Exception("Service overloaded")

    async def process_queue(self):
        """Process queued tasks"""
        while True:
            try:
                task, args, kwargs = await self.queue.get()
                async with self.acquire_slot():
                    if asyncio.iscoroutinefunction(task):
                        await task(*args, **kwargs)
                    else:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, task, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error processing queued task: {e}")


async def parallel_execute(
    tasks: List[Callable],
    max_concurrent: Optional[int] = None,
    timeout: Optional[float] = None,
) -> List[Any]:
    """
    Execute multiple tasks in parallel using asyncio.gather()

    Args:
        tasks: List of callables to execute
        max_concurrent: Maximum concurrent executions
        timeout: Overall timeout for all tasks

    Returns:
        List of results in same order as tasks
    """
    if not tasks:
        return []

    # Convert sync functions to async if needed
    async def execute_task(task):
        if asyncio.iscoroutinefunction(task):
            return await task()
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, task)

    # Execute tasks
    if max_concurrent:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_task(task):
            async with semaphore:
                return await execute_task(task)

        task_coros = [limited_task(task) for task in tasks]
    else:
        task_coros = [execute_task(task) for task in tasks]

    # Execute with timeout if specified
    if timeout:
        return await asyncio.wait_for(asyncio.gather(*task_coros), timeout=timeout)
    else:
        return await asyncio.gather(*task_coros)


async def batch_process(
    items: List[Any],
    processor: Callable,
    batch_size: int = 10,
    max_concurrent_batches: Optional[int] = None,
) -> List[Any]:
    """
    Process items in batches with parallel execution

    Args:
        items: List of items to process
        processor: Function to process each item
        batch_size: Number of items per batch
        max_concurrent_batches: Maximum concurrent batches

    Returns:
        List of processed results
    """
    if not items:
        return []

    # Split items into batches
    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    async def process_batch(batch):
        return await parallel_execute(
            [lambda item=item: processor(item) for item in batch]
        )

    # Process batches in parallel
    batch_results = await parallel_execute(
        [process_batch(batch) for batch in batches],
        max_concurrent=max_concurrent_batches,
    )

    # Flatten results
    return [item for batch in batch_results for item in batch]


@asynccontextmanager
async def timeout_context(timeout: float):
    """Context manager for timeout handling"""
    try:
        yield
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout} seconds")
        raise


# Global instances
default_circuit_breaker = CircuitBreaker(CircuitBreakerConfig())
default_backpressure_manager = BackpressureManager()


# Decorators for easy usage
def with_circuit_breaker(config: Optional[CircuitBreakerConfig] = None):
    """Decorator to add circuit breaker to function"""
    circuit = CircuitBreaker(config or CircuitBreakerConfig())

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            return await circuit.call(func, *args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(circuit.call(func, *args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def with_backpressure(max_concurrent: int = 100):
    """Decorator to add backpressure to functions"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with BackpressureManager(max_concurrent).acquire_slot():
                return await func(*args, **kwargs)

        return wrapper

    return decorator


async def async_retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs,
) -> T:
    """
    Retry an async function with exponential backoff

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
        *args: Arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, func, *args, **kwargs)

        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {current_delay:.2f}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(
                    f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                )
                raise last_exception

    # This should never be reached, but just in case
    raise last_exception
