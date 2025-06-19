import logging
from typing import Any, Dict
from src.backend.agents.agent_factory import AgentFactory
from src.backend.agents.agent_registry import AgentRegistry
from src.backend.agents.error_types import AgentError, EnhancedAgentResponse
from .orchestrator_errors import AgentProcessingError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AgentRouter:
    def __init__(self, agent_factory: AgentFactory, agent_registry: AgentRegistry):
        self.agent_factory = agent_factory
        self.agent_registry = agent_registry
        
        # Register intent mappings with the registry
        self.agent_registry.register_intent_to_agent_mapping("cooking", "Chef")
        self.agent_registry.register_intent_to_agent_mapping("weather", "Weather")
        self.agent_registry.register_intent_to_agent_mapping("document", "RAG")
        self.agent_registry.register_intent_to_agent_mapping("image", "OCR")
        self.agent_registry.register_intent_to_agent_mapping("shopping", "Categorization")
        self.agent_registry.register_intent_to_agent_mapping("meal_plan", "MealPlanner")
        self.agent_registry.register_intent_to_agent_mapping("search", "Search")
        self.agent_registry.register_intent_to_agent_mapping("analytics", "Analytics")
        self.agent_registry.register_intent_to_agent_mapping("general", "Chef")

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
            # Przyjmujemy, że context jest wystarczający dla agenta, 
            # a agent sam wyciągnie z niego potrzebne dane, w tym `query` lub `message`.
            response = await agent.process(context) 

            # Upewnij się, że AgentResponse jest właściwie obsługiwany
            if isinstance(response, EnhancedAgentResponse):
                return {
                    "response": response.dict(), # Zwracamy słownik z obiektu Pydantic
                    "metadata": {
                        "intent": intent_type,
                        "agent": agent_type,
                        "entities": intent.get("entities", {}),
                        "fallback_used": False if agent_type == self.agent_registry.get_agent_type_for_intent(intent_type) else True
                    }
                }
            else: # Jeśli agent zwróci stare AgentResponse lub inny typ
                 return {
                    "response": response.to_dict(),
                    "metadata": {
                        "intent": intent_type,
                        "agent": agent_type,
                        "entities": intent.get("entities", {}),
                        "fallback_used": False if agent_type == self.agent_registry.get_agent_type_for_intent(intent_type) else True
                    }
                }

        except AgentError as e:
            logger.error(f"AgentError during processing with agent {agent_type}: {str(e)}", exc_info=True)
            # Użyj bardziej szczegółowego błędu z orchestrator_errors
            raise AgentProcessingError(f"Error processing request: {str(e)}", details={"agent": agent_type, "intent": intent_type}) from e
        except Exception as e:
            logger.error(f"Unexpected error processing request with agent {agent_type}: {str(e)}", exc_info=True)
            raise AgentProcessingError(f"Przepraszam, wystąpił nieoczekiwany błąd podczas przetwarzania żądania.", 
                                      details={"agent": agent_type, "intent": intent_type, "exception": str(e)}) from e

    # Dodaj prywatną metodę pomocniczą do generowania odpowiedzi fallback
    def _create_fallback_response(self, intent_type: str, error_message: str) -> Dict[str, Any]:
        return {
            "response": {
                "success": False,
                "error": f"Przepraszam, wystąpił problem podczas przetwarzania żądania: {error_message}",
                "text": "Przepraszam, wystąpił problem podczas przetwarzania żądania.",
                "message": "Processing failed due to an error."
            },
            "metadata": {
                "intent": intent_type,
                "agent": "FallbackHandler",
                "entities": {},
                "fallback_used": True
            }
        }
