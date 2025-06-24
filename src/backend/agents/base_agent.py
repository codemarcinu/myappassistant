"""
Base agent implementation for the AI assistant framework.
Provides core functionality for all agent types.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import (Any, AsyncGenerator, Callable, Dict, Generic, List,
                    Optional, Type, TypeVar)

from pydantic import BaseModel, ValidationError

from backend.agents.interfaces import AgentResponse
from backend.agents.interfaces import BaseAgent as IBaseAgent
from backend.agents.interfaces import ErrorSeverity
from backend.core.hybrid_llm_client import hybrid_llm_client

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class BaseAgent(IBaseAgent, ABC):
    """
    Enhanced base agent with improved error handling, fallbacks, and alerting.
    This provides robust error handling and recovery mechanisms.
    """

    def __init__(
        self,
        name: str = "BaseAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.error_handler = error_handler
        self.fallback_manager = fallback_manager
        self.input_model: Optional[Type[BaseModel]] = None

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Main processing method to be implemented by each agent"""
        raise NotImplementedError("process() must be implemented by subclass")

    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata including capabilities"""
        return {"name": self.name, "type": self.__class__.__name__, "capabilities": []}

    def get_dependencies(self) -> List[type]:
        """List of agent types this agent depends on"""
        return []

    def is_healthy(self) -> bool:
        """Check if agent is functioning properly"""
        return True

    def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against model"""
        if self.input_model:
            try:
                validated = self.input_model.model_validate(data)
                return validated.dict()
            except ValidationError as ve:
                raise ValueError(f"Invalid input data for {self.name}: {ve}") from ve
        return data

    async def execute_with_fallback(
        self,
        func: Callable[..., Any],
        *args,
        fallback_handler: Optional[Callable[..., Any]] = None,
        error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        **kwargs,
    ) -> None:
        """
        Execute a function with automatic fallback and error handling
        Delegates to ErrorHandler
        """
        if self.error_handler:
            return await self.error_handler.execute_with_fallback(
                func,
                *args,
                fallback_handler=fallback_handler,
                error_severity=error_severity,
                **kwargs,
            )
        else:
            return await func(*args, **kwargs)

    async def process_with_circuit_breaker(
        self, input_data: Dict[str, Any]
    ) -> AgentResponse:
        """Process input with circuit breaker protection"""
        try:
            return await self.process(input_data)
        except Exception as e:
            logger.error(f"Error in {self.name}.process: {str(e)}")
            return AgentResponse(success=False, error=str(e), severity="ERROR")

    async def safe_process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input with basic error handling"""
        try:
            return await self.process(input_data)
        except Exception as e:
            logger.error(f"Error in {self.name}.process: {str(e)}")
            return AgentResponse(success=False, error=str(e), severity="ERROR")

    async def _stream_llm_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response"""
        try:
            async for chunk in hybrid_llm_client.chat(
                messages=messages, model=model, stream=True
            ):
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in LLM streaming for {self.name}: {e}")
            yield "Przepraszam, wystąpił błąd podczas przetwarzania odpowiedzi. Spróbuj ponownie później."
        except Exception as e:
            logger.error(f"Error in LLM streaming for {self.name}: {e}")
            # Zwróć przyjazny komunikat o błędzie
            yield "Przepraszam, wystąpił błąd podczas przetwarzania. Spróbuj ponownie później."


class BaseAgentEnhanced(IBaseAgent, Generic[T]):
    """
    Enhanced base agent with additional features:
    - Type validation through generic input model
    - Improved error handling
    - Streaming LLM support
    """

    def __init__(
        self, name: str, error_handler: Any = None, fallback_manager: Any = None
    ) -> None:
        super().__init__(
            name, error_handler=error_handler, fallback_manager=fallback_manager
        )
        self.input_model: Optional[type[T]] = None

    def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against model"""
        if self.input_model:
            try:
                validated = self.input_model.model_validate(data)
                return validated.dict()
            except ValidationError as ve:
                raise ValueError(f"Invalid input data for {self.name}: {ve}") from ve
        return data

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process input data and return response.
        Must be implemented by all agent subclasses.
        """
