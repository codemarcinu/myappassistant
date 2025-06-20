import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .interfaces import (
    AgentResponse,
    AgentType,
    IAgentRouter,
    IntentData,
    MemoryContext,
)

logger = logging.getLogger(__name__)


class AgentRouter(IAgentRouter):
    """Implementation of IAgentRouter using dependency injection and our new interfaces"""

    def __init__(self):
        self._agents: Dict[AgentType, BaseAgent] = {}
        self._fallback_agent: Optional[BaseAgent] = None

    def register_agent(self, agent_type: AgentType, agent: BaseAgent):
        """Register an agent implementation"""
        if not isinstance(agent, BaseAgent):
            raise ValueError("Agent must implement BaseAgent interface")
        self._agents[agent_type] = agent
        logger.info(f"Registered agent for type: {agent_type.value}")

    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Get registered agent by type"""
        agent = self._agents.get(agent_type)
        if agent is None:
            raise ValueError(f"No agent registered for type: {agent_type.value}")
        return agent

    def set_fallback_agent(self, agent: BaseAgent):
        """Set fallback agent for unknown intents"""
        self._fallback_agent = agent
        logger.info("Fallback agent set")

    async def route_to_agent(
        self,
        intent: IntentData,
        context: MemoryContext,
        user_command: str = "",
        use_perplexity: bool = False,
        use_bielik: bool = True,
    ) -> AgentResponse:
        """Route intent to appropriate agent and return response"""
        try:
            # Map intent type to agent type
            agent_type = self._map_intent_to_agent_type(intent.type)

            # Get the appropriate agent
            agent = self._agents.get(agent_type)

            if agent is None:
                if self._fallback_agent:
                    logger.warning(
                        f"No agent found for type {agent_type}, using fallback"
                    )
                    agent = self._fallback_agent
                else:
                    return AgentResponse(
                        success=False,
                        error=f"No agent available for intent type: {intent.type}",
                        severity="ERROR",
                    )

            # Prepare input data for agent based on agent type
            input_data = self._prepare_agent_input(
                agent_type, user_command, intent, context
            )
            input_data["use_perplexity"] = (
                use_perplexity  # Przekazujemy flagę do agenta
            )
            input_data["use_bielik"] = use_bielik  # Przekazujemy flagę modelu do agenta

            # Process with agent
            logger.info(f"Routing intent '{intent.type}' to agent {agent_type.value}")
            response = await agent.process(input_data)

            return response

        except Exception as e:
            logger.error(f"Error routing to agent: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Błąd routingu do agenta: {str(e)}",
                severity="ERROR",
            )

    def _prepare_agent_input(
        self,
        agent_type: AgentType,
        user_command: str,
        intent: IntentData,
        context: MemoryContext,
    ) -> Dict[str, Any]:
        """Prepare input data specific to agent type"""
        base_data = {
            "query": user_command,
            "intent": intent.type,
            "entities": intent.entities,
            "confidence": intent.confidence,
            "session_id": context.session_id,
            "context": context.history[-10:] if context.history else [],
        }

        if agent_type == AgentType.CHEF:
            # For ChefAgent, extract ingredients from user command or provide default
            ingredients = self._extract_ingredients_from_query(user_command)
            return {
                **base_data,
                "ingredients": ingredients,
                "dietary_restrictions": None,
                "model": "gemma3:12b",
            }
        elif agent_type == AgentType.RAG:
            # For RAGAgent, use query as is
            return {**base_data, "query": user_command}
        else:
            # For other agents, use base data
            return base_data

    def _extract_ingredients_from_query(self, query: str) -> List[str]:
        """Extract ingredients from user query"""
        # Simple extraction - look for common ingredient words
        query_lower = query.lower()
        common_ingredients = [
            "jajka",
            "mleko",
            "mąka",
            "cukier",
            "sól",
            "pieprz",
            "olej",
            "masło",
            "cebula",
            "czosnek",
            "pomidory",
            "ziemniaki",
            "marchew",
            "kurczak",
            "wołowina",
            "wieprzowina",
            "ryż",
            "makaron",
            "ser",
            "śmietana",
        ]

        found_ingredients = []
        for ingredient in common_ingredients:
            if ingredient in query_lower:
                found_ingredients.append(ingredient)

        # If no ingredients found, provide some defaults
        if not found_ingredients:
            found_ingredients = ["jajka", "mleko", "mąka"]

        return found_ingredients

    def _map_intent_to_agent_type(self, intent_type: str) -> AgentType:
        """Map intent type to agent type"""
        intent_mapping = {
            # Nowe typy konwersacji
            "general_conversation": AgentType.GENERAL_CONVERSATION,
            "shopping_conversation": AgentType.CATEGORIZATION,
            "food_conversation": AgentType.CHEF,
            "information_query": AgentType.SEARCH,
            # Istniejące typy
            "cooking": AgentType.CHEF,
            "weather": AgentType.WEATHER,
            "search": AgentType.SEARCH,
            "rag": AgentType.RAG,
            "ocr": AgentType.OCR,
            "categorization": AgentType.CATEGORIZATION,
            "meal_planning": AgentType.MEAL_PLANNER,
            "analytics": AgentType.ANALYTICS,
            # Fallback
            "general": AgentType.GENERAL_CONVERSATION,  # Default to GeneralConversation
        }

        return intent_mapping.get(intent_type, AgentType.GENERAL_CONVERSATION)

    def get_registered_agents(self) -> Dict[AgentType, BaseAgent]:
        """Get all registered agents"""
        return self._agents.copy()

    def is_agent_registered(self, agent_type: AgentType) -> bool:
        """Check if agent type is registered"""
        return agent_type in self._agents
