import logging
from typing import Any, Dict, Literal, Optional, TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.agent_factory import AgentFactory
from backend.agents.state import ConversationState
from backend.core import crud

IntentType: TypeAlias = Literal[
    "WEATHER", "SEARCH", "UPDATE_ITEM", "DELETE_ITEM", "UNKNOWN"
]

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes requests to appropriate agents based on intent and state."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_factory = AgentFactory()

    async def route(
        self, user_command: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Main routing method that delegates to specialized agents."""
        try:
            # First try keyword-based routing for performance
            if state.agent_states.get("weather", True) and self._is_weather_query(
                user_command
            ):
                return await self._route_to_weather_agent(user_command, state)

            if state.agent_states.get("search", True) and self._is_search_query(
                user_command
            ):
                return await self._route_to_search_agent(user_command, state)

            # Fall back to intent-based routing
            return await self._route_by_intent(user_command, state)

        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {
                "response": "Przepraszam, wystąpił problem z przetwarzaniem polecenia.",
                "state": state.to_dict(),
            }

    async def _route_to_weather_agent(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        weather_agent = self.agent_factory.create_agent("weather")
        try:
            response = await weather_agent.process(
                {"query": query, "model": state.current_model}
            )
            return self._format_agent_response(response, state)
        except Exception as e:
            logger.error(f"Weather agent error: {e}")
            return {
                "response": "Wystąpił błąd podczas przetwarzania zapytania pogodowego",
                "state": state.to_dict(),
            }

    async def _route_to_search_agent(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        search_agent = self.agent_factory.create_agent("search")
        try:
            response = await search_agent.process(
                {"query": query, "model": state.current_model}
            )
            return self._format_agent_response(response, state)
        except Exception as e:
            logger.error(f"Search agent error: {e}")
            return {
                "response": "Wystąpił błąd podczas przetwarzania wyszukiwania",
                "state": state.to_dict(),
            }

    async def _route_by_intent(
        self, user_command: str, state: ConversationState
    ) -> Dict[str, Any]:
        intent_recognizer = IntentRecognizer(self.db)
        intent_data = await intent_recognizer.recognize(user_command)

        if intent_data.get("requires_clarification"):
            return intent_data

        entity_extractor = EntityExtractor(self.db)
        entities = await entity_extractor.extract(user_command, intent_data["intent"])

        response_formatter = ResponseFormatter()
        return await response_formatter.format_response(
            intent=intent_data["intent"], entities=entities, state=state, db=self.db
        )

    def _is_weather_query(self, query: str) -> bool:
        weather_keywords = ["pogoda", "deszcz", "temperatura"]
        return any(kw in query.lower() for kw in weather_keywords)

    def _is_search_query(self, query: str) -> bool:
        search_keywords = ["wyszukaj", "znajdź", "szukaj"]
        return any(kw in query.lower() for kw in search_keywords)

    def _format_agent_response(
        self, response: Any, state: ConversationState
    ) -> Dict[str, Any]:
        """Format response from both legacy and enhanced agents"""
        if not response.success:
            return {
                "response": response.error
                or "Wystąpił problem z przetwarzaniem żądania.",
                "state": state.to_dict(),
            }

        # Handle streaming response
        if response.text_stream:
            return response.text_stream

        # Handle structured data response
        if hasattr(response, "data"):
            return {
                "response": response.message or "Żądanie przetworzone pomyślnie",
                "data": response.data,
                "state": state.to_dict(),
            }

        return {"response": "Żądanie przetworzone pomyślnie", "state": state.to_dict()}


class IntentRecognizer:
    """Recognizes user intent from natural language commands."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def recognize(self, user_command: str) -> Dict[str, Any]:
        from backend.agents.prompts import get_intent_recognition_prompt
        from backend.agents.utils import extract_json_from_text
        from backend.core.llm_client import llm_client

        prompt = get_intent_recognition_prompt(user_command)
        intent_response = await llm_client.chat(
            model="gemma3:12b",
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )

        intent_data = extract_json_from_text(intent_response)
        return {
            "intent": intent_data.get("intent", "UNKNOWN"),
            "requires_clarification": False,
        }


class EntityExtractor:
    """Extracts entities from user commands based on recognized intent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def extract(self, user_command: str, intent: str) -> Dict[str, Any]:
        from backend.agents.prompts import get_entity_extraction_prompt
        from backend.agents.utils import extract_json_from_text
        from backend.core.llm_client import llm_client

        prompt = get_entity_extraction_prompt(user_command, intent)
        entities_response = await llm_client.chat(
            model="gemma3:12b",
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )

        return extract_json_from_text(entities_response)


class ResponseFormatter:
    """Formats consistent responses from agent outputs."""

    async def format_response(
        self,
        intent: str,
        entities: Dict[str, Any],
        state: ConversationState,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        from backend.agents.tools.tools import execute_database_action

        if intent in ["UPDATE_ITEM", "DELETE_ITEM"]:
            _ = await execute_database_action(
                db=db, intent=intent, target_object=None, entities=entities
            )
            action_word = "Zaktualizowałem" if "UPDATE" in intent else "Usunąłem"
            return {"response": f"{action_word} wpis.", "state": state.to_dict()}

        return {
            "response": "Nie rozpoznano specyficznej akcji.",
            "state": state.to_dict(),
        }


class ConversationStateManager:
    """Manages conversation state and history."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_state(self, session_id: str) -> ConversationState:
        conversation = await crud.get_conversation_by_session_id(self.db, session_id)
        if not conversation:
            conversation = await crud.create_conversation(self.db, session_id)

        state = ConversationState(session_id=session_id)
        # TODO: Load state from conversation history
        return state

    async def save_state(self, state: ConversationState) -> None:
        # TODO: Implement state persistence
        pass


class Orchestrator:
    """Main orchestrator class that coordinates the specialized components."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_router = AgentRouter(db)
        self.state_manager = ConversationStateManager(db)

    async def process_command(
        self,
        user_command: str,
        session_id: str,
        file_info: Optional[Dict] = None,
        agent_states: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """Main entry point to process a user's command."""
        state = await self.state_manager.get_state(session_id)

        if agent_states:
            state.agent_states = agent_states

        # Set appropriate model based on active agents
        if state.agent_states.get("shopping", False) or state.agent_states.get(
            "cooking", False
        ):
            state.current_model = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
        else:
            state.current_model = "gemma3:12b"

        try:
            # Route the command to appropriate handler
            response = await self.agent_router.route(user_command, state)

            # Save updated state
            await self.state_manager.save_state(state)

            return response

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "response": "Wystąpił błąd podczas przetwarzania polecenia.",
                "state": state.to_dict(),
            }


__all__ = [
    "IntentType",
    "AgentRouter",
    "IntentRecognizer",
    "EntityExtractor",
    "ResponseFormatter",
    "ConversationStateManager",
    "Orchestrator",
]
