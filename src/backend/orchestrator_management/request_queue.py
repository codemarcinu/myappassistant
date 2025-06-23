import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class QueuedRequest:
    id: str
    user_command: str
    session_id: str
    file_info: Optional[Dict]
    agent_states: Optional[Dict[str, bool]]
    timestamp: float
    retry_count: int = 0


class RequestQueue:
    def __init__(self, max_queue_size: int = 1000, max_retries: int = 3) -> None:
        self.queue: asyncio.Queue[QueuedRequest] = asyncio.Queue(maxsize=max_queue_size)
        self.max_retries = max_retries
        self.dead_letter_queue: asyncio.Queue[QueuedRequest] = asyncio.Queue()
        logger.info(
            f"RequestQueue initialized with max_queue_size={max_queue_size}, max_retries={max_retries}"
        )

    async def enqueue_request(
        self,
        user_command: str,
        session_id: str,
        file_info: Optional[Dict] = None,
        agent_states: Optional[Dict[str, bool]] = None,
    ) -> str:
        """Dodaje żądanie do kolejki. Zwraca ID żądania."""
        request_id = str(uuid.uuid4())
        request = QueuedRequest(
            id=request_id,
            user_command=user_command,
            session_id=session_id,
            file_info=file_info,
            agent_states=agent_states,
            timestamp=time.time(),
        )
        try:
            self.queue.put_nowait(
                request
            )  # put_nowait aby nie blokować, jeśli kolejka pełna
            logger.debug(f"Request '{request_id}' enqueued successfully.")
        except asyncio.QueueFull:
            await self.dead_letter_queue.put(request)
            logger.warning(
                f"Request queue is full. Request '{request_id}' moved to dead letter queue."
            )
            raise Exception("Service temporarily unavailable, queue is full.")
        return request_id

    async def dequeue_request(self) -> Optional[QueuedRequest]:
        """Pobiera następne żądanie do przetworzenia."""
        try:
            request = await asyncio.wait_for(
                self.queue.get(), timeout=1.0
            )  # krótki timeout
            logger.debug(f"Request '{request.id}' dequeued.")
            return request
        except asyncio.TimeoutError:
            return None  # Kolejka pusta
        except Exception as e:
            logger.error(f"Error dequeuing request: {e}", exc_info=True)
            return None

    async def requeue_request(self, request: QueuedRequest, error_reason: str) -> None:
        """Ponownie dodaje żądanie do kolejki, jeśli próba przetwarzania się nie powiodła."""
        request.retry_count += 1
        if request.retry_count <= self.max_retries:
            await self.queue.put(request)
            logger.warning(
                f"Request '{request.id}' failed (reason: {error_reason}). Requeuing (retry {request.retry_count}/{self.max_retries})."
            )
        else:
            await self.dead_letter_queue.put(request)
            logger.error(
                f"Request '{request.id}' failed after {self.max_retries} retries. Moving to dead letter queue."
            )

    async def get_dead_letter_queue_size(self) -> int:
        return self.dead_letter_queue.qsize()

    async def get_queue_size(self) -> int:
        return self.queue.qsize()


# Global instance of the request queue
request_queue: RequestQueue = RequestQueue()
