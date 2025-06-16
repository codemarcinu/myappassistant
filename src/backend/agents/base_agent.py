import asyncio
import logging
from abc import ABC, abstractmethod
from functools import wraps  # noqa: F401
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

from pydantic import BaseModel, ValidationError

from ..core.llm_client import LLMClient

# Define type variable at top level
T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Standardowa odpowiedź agenta"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    text_stream: Optional[AsyncGenerator[str, None]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True


class EnhancedBaseAgent(ABC, Generic[T]):
    """Ulepszona bazowa klasa dla wszystkich agentów"""

    _llm_client: LLMClient

    def __init__(self, name: str):
        self.name = name
        self.input_model: Optional[type[T]] = None

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Główna metoda przetwarzania - musi być zaimplementowana przez każdy agent"""
        pass

    def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardowa walidacja danych wejściowych"""
        if self.input_model:
            try:
                return self.input_model.parse_obj(data).dict()
            except ValidationError as ve:
                _ = {
                    "error_type": "validation_error",
                    "errors": ve.errors(),
                }
                raise ValueError("Invalid input data") from ve
        return data

    def _handle_error(self, error: Exception) -> AgentResponse:
        """Standardowa obsługa błędów"""
        logger.error(f"Error in {self.name}: {str(error)}", exc_info=True)

        error_details = {
            "agent": self.name,
            "error_type": type(error).__name__,
            "message": str(error),
        }

        if isinstance(error, ValidationError):
            error_details.update(
                {"error_type": "validation_error", "errors": error.errors()}
            )

        return AgentResponse(
            success=False,
            error=f"Error in {self.name}: {str(error)}",
            error_details=error_details,
        )

    async def _stream_llm_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> AsyncGenerator[str, None]:
        """Ujednolicona metoda strumieniowania odpowiedzi LLM"""
        attempt = 0

        while attempt < retries:
            try:
                async for chunk in self._llm_client.generate_stream(
                    model=model, messages=messages
                ):
                    yield chunk["message"]["content"]
                return
            except Exception as e:
                logger.debug(f"LLM streaming error: {str(e)}")
                attempt += 1
                if attempt < retries:
                    wait_time = backoff_factor * (2 ** (attempt - 1))
                    logger.warning(
                        f"LLM streaming attempt {attempt} failed, retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)

        logger.error(f"LLM streaming failed after {retries} attempts")
        yield f"Error: Failed to generate response after {retries} attempts"

    def __str__(self):
        name_str = str(self.name) if not isinstance(self.name, tuple) else self.name[0]
        return f"{self.__class__.__name__}(name={name_str})"


if TYPE_CHECKING:
    BaseAgent = EnhancedBaseAgent[BaseModel]
else:
    BaseAgent = "EnhancedBaseAgent[BaseModel]"

__all__ = ["BaseAgent", "EnhancedBaseAgent", "AgentResponse"]
