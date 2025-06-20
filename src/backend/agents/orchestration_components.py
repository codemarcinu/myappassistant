import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from .interfaces import AgentResponse, BaseAgent, IntentData, MemoryContext

logger = logging.getLogger(__name__)


class IIntentDetector(ABC):
    @abstractmethod
    async def detect_intent(self, query: str, context: MemoryContext) -> IntentData:
        """Detects user intent based on query and context."""


class IAgentRouter(ABC):
    @abstractmethod
    async def route_to_agent(
        self, intent: IntentData, context: MemoryContext
    ) -> AgentResponse:
        """Routes the intent to the appropriate agent and returns its response."""

    @abstractmethod
    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Register an agent implementation for a specific type"""

    @abstractmethod
    def get_agent(self, agent_type: str) -> BaseAgent:
        """Get registered agent by type"""


class IMemoryManager(ABC):
    @abstractmethod
    async def store_context(self, context: MemoryContext) -> None:
        """Store context for later retrieval"""

    @abstractmethod
    async def retrieve_context(self, session_id: str) -> Optional[MemoryContext]:
        """Retrieve context for session if it exists"""

    @abstractmethod
    async def update_context(
        self, context: MemoryContext, new_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update existing context with optional new data"""

    @abstractmethod
    async def clear_context(self, session_id: str) -> None:
        """Clear context for session"""


class IResponseGenerator(ABC):
    @abstractmethod
    async def generate_response(
        self, context: MemoryContext, agent_response: AgentResponse
    ) -> AgentResponse:
        """Generate final response based on context and agent response"""


class SimpleIntentDetector(IIntentDetector):
    async def detect_intent(self, query: str, context: MemoryContext) -> IntentData:
        query_lower = query.lower()
        if "przepis" in query_lower:
            return IntentData("recipe_request")
        elif "dodaj" in query_lower or "kup" in query_lower:
            return IntentData("add_to_list")
        return IntentData("general_query")


class BasicMemoryManager(IMemoryManager):
    def __init__(self):
        self.contexts = {}

    async def get_context(self, session_id: str) -> MemoryContext:
        if session_id not in self.contexts:
            self.contexts[session_id] = MemoryContext(session_id)
        return self.contexts[session_id]

    async def update_context(
        self, context: MemoryContext, new_data: Optional[Dict[str, Any]] = None
    ):
        if new_data:
            context.history.append(
                {"timestamp": datetime.now().isoformat(), "data": new_data}
            )


class BasicResponseGenerator(IResponseGenerator):
    async def generate_response(
        self, agent_response: Dict[str, Any], context: MemoryContext
    ) -> str:
        if "response" in agent_response:
            return agent_response["response"]
        return "Przepraszam, wystąpił problem podczas przetwarzania żądania."
