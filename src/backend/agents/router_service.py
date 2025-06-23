import logging
from typing import Any, Dict

from .agent_factory import AgentFactory
from .agent_registry import AgentRegistry
from .error_types import AgentError, AgentProcessingError
from .interfaces import AgentResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AgentRouter:
    def __init__(self, agent_factory: AgentFactory, agent_registry: AgentRegistry) -> None:
        self.agent_factory = agent_factory
        self.agent_registry = agent_registry

        # Check if agent classes are registered
        registered_types = self.agent_registry.get_all_registered_agent_types()
        logger.info(f"Registered agent types: {registered_types}")

        # Register intent mappings with the registry
        self.agent_registry.register_intent_to_agent_mapping("cooking", "Chef")
        self.agent_registry.register_intent_to_agent_mapping("weather", "Weather")
        self.agent_registry.register_intent_to_agent_mapping("document", "RAG")
        self.agent_registry.register_intent_to_agent_mapping("image", "OCR")
        self.agent_registry.register_intent_to_agent_mapping(
            "shopping", "Categorization"
        )
        self.agent_registry.register_intent_to_agent_mapping("meal_plan", "MealPlanner")
        self.agent_registry.register_intent_to_agent_mapping("search", "Search")
        self.agent_registry.register_intent_to_agent_mapping("analytics", "Analytics")
        self.agent_registry.register_intent_to_agent_mapping("general", "Chef")

    def register_agent(self, agent_type: str, agent: Any) -> None:
        """Register an agent implementation for a specific type"""
        # This method is required by the orchestrator but not used in this implementation
        # as agents are created dynamically by the factory
        logger.info(f"Agent registration requested for type: {agent_type}")
        pass

    def get_agent(self, agent_type: str) -> None:
        """Get registered agent by type"""
        # This method is required by the orchestrator but not used in this implementation
        # as agents are created dynamically by the factory
        logger.info(f"Agent retrieval requested for type: {agent_type}")
        return None

    def set_fallback_agent(self, agent: Any) -> None:
        """Set fallback agent for unknown intents"""
        # This method is required by the orchestrator but not used in this implementation
        # as agents are created dynamically by the factory
        logger.info("Fallback agent set")
        pass

    async def route_to_agent(
        self, intent: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        intent_type = intent.get("type", "general")
        agent_type = self.agent_registry.get_agent_type_for_intent(intent_type)

        try:
            # Walidacja przed utworzeniem agenta
            if agent_type not in self.agent_registry.get_all_registered_agent_types():
                logger.warning(
                    f"Agent type '{agent_type}' not found in factory registry for intent '{intent_type}'. "
                    f"Falling back to default agent 'Chef'."
                )
                agent_type = "Chef"  # Fallback na zawsze dostępny agent

            logger.debug(f"Creating agent: {agent_type}")
            agent = self.agent_factory.create_agent(agent_type)

            if agent is None:
                logger.error(f"Agent factory returned None for type: {agent_type}")
                return self._create_fallback_response(
                    intent_type, "Agent creation failed"
                )

            logger.debug(f"Agent created successfully: {type(agent)}")

            # Przyjmujemy, że context jest wystarczający dla agenta,
            # a agent sam wyciągnie z niego potrzebne dane, w tym `query` lub `message`.
            logger.debug(f"Processing with agent: {agent_type}")
            response = await agent.process(context)

            logger.debug(f"Agent response: {type(response)} - {response}")

            # Upewnij się, że AgentResponse jest właściwie obsługiwany
            if isinstance(response, AgentResponse):
                return {
                    "response": response.model_dump(),  # Używamy model_dump() dla Pydantic v2
                    "metadata": {
                        "intent": intent_type,
                        "agent": agent_type,
                        "entities": intent.get("entities", {}),
                        "fallback_used": (
                            False
                            if agent_type
                            == self.agent_registry.get_agent_type_for_intent(
                                intent_type
                            )
                            else True
                        ),
                    },
                }
            else:  # Jeśli agent zwróci inny typ
                return {
                    "response": (
                        response if isinstance(response, dict) else str(response)
                    ),
                    "metadata": {
                        "intent": intent_type,
                        "agent": agent_type,
                        "entities": intent.get("entities", {}),
                        "fallback_used": (
                            False
                            if agent_type
                            == self.agent_registry.get_agent_type_for_intent(
                                intent_type
                            )
                            else True
                        ),
                    },
                }

        except AgentError as e:
            logger.error(
                f"AgentError during processing with agent {agent_type}: {str(e)}",
                exc_info=True,
            )
            # Użyj bardziej szczegółowego błędu z error_types
            raise AgentProcessingError(
                f"Error processing request: {str(e)}",
                agent_type=agent_type,
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error processing request with agent {agent_type}: {str(e)}",
                exc_info=True,
            )
            raise AgentProcessingError(
                "Przepraszam, wystąpił nieoczekiwany błąd podczas przetwarzania żądania.",
                agent_type=agent_type,
            ) from e

    # Dodaj prywatną metodę pomocniczą do generowania odpowiedzi fallback
    def _create_fallback_response(
        self, intent_type: str, error_message: str
    ) -> Dict[str, Any]:
        return {
            "response": {
                "success": False,
                "error": f"Przepraszam, wystąpił problem podczas przetwarzania żądania: {error_message}",
                "text": "Przepraszam, wystąpił problem podczas przetwarzania żądania.",
                "message": "Processing failed due to an error.",
            },
            "metadata": {
                "intent": intent_type,
                "agent": "FallbackHandler",
                "entities": {},
                "fallback_used": True,
            },
        }
