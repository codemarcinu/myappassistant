import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from backend.agents.interfaces import AgentResponse, IntentData, MemoryContext

logger = logging.getLogger(__name__)


class IIntentDetector(ABC):
    @abstractmethod
    async def detect_intent(self, query: str, context: MemoryContext) -> IntentData:
        """Detects user intent based on query and context."""


class IMemoryManager(ABC):
    @abstractmethod
    async def get_context(self, session_id: str) -> MemoryContext:
        """Retrieves or creates a memory context for a session."""

    @abstractmethod
    async def update_context(
        self, context: MemoryContext, new_data: Dict[str, Any]
    ) -> None:
        """Updates the memory context with new data."""


class IResponseGenerator(ABC):
    @abstractmethod
    async def generate_response(
        self, context: MemoryContext, last_response: AgentResponse
    ) -> AgentResponse:
        """Generates a final response based on the conversation context."""


class SimpleIntentDetector(IIntentDetector):
    async def detect_intent(self, query: str, context: MemoryContext) -> IntentData:
        query_lower = query.lower()
        if "przepis" in query_lower:
            return IntentData("recipe_request")
        elif "dodaj" in query_lower or "kup" in query_lower:
            return IntentData("add_to_list")
        return IntentData("general_query")


class BasicMemoryManager(IMemoryManager):
    def __init__(self) -> None:
        self.contexts = {}

    async def get_context(self, session_id: str) -> MemoryContext:
        if session_id not in self.contexts:
            self.contexts[session_id] = MemoryContext(session_id)
        return self.contexts[session_id]

    async def update_context(
        self, context: MemoryContext, new_data: Dict[str, Any]
    ) -> None:
        if new_data:
            context.history.append(
                {"timestamp": datetime.now().isoformat(), "data": new_data}
            )


class BasicResponseGenerator(IResponseGenerator):
    async def generate_response(
        self, context: MemoryContext, agent_response: AgentResponse
    ) -> AgentResponse:
        if agent_response.text:
            return AgentResponse(success=True, text=agent_response.text)
        return AgentResponse(
            success=False,
            error="Przepraszam, wystąpił problem podczas przetwarzania żądania.",
        )
