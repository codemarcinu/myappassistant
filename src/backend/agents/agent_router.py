import logging
from typing import Any, Dict, Optional

from .interfaces import AgentResponse, AgentType
from .interfaces import BaseAgent as IBaseAgent
from .interfaces import IAgentRouter, IntentData, MemoryContext

logger = logging.getLogger(__name__)


class AgentRouter(IAgentRouter):
    """Implementation of IAgentRouter using dependency injection and our new interfaces"""

    def __init__(self) -> None:
        self._agents: Dict[AgentType, IBaseAgent] = {}
        self._fallback_agent: Optional[IBaseAgent] = None

    def register_agent(self, agent_type: AgentType, agent: IBaseAgent) -> None:
        """Register an agent implementation"""
        if not isinstance(agent, IBaseAgent):
            raise ValueError("Agent must implement BaseAgent interface")
        self._agents[agent_type] = agent
        logger.info(f"Registered agent for type: {agent_type.value}")

    def get_agent(self, agent_type: AgentType) -> IBaseAgent:
        """Get registered agent by type"""
        agent = self._agents.get(agent_type)
        if agent is None:
            raise ValueError(f"No agent registered for type: {agent_type.value}")
        return agent

    def set_fallback_agent(self, agent: IBaseAgent) -> None:
        """Set fallback agent for unknown intents"""
        self._fallback_agent = agent
        logger.info("Fallback agent set")

    async def route_to_agent(
        self, intent: IntentData, context: MemoryContext, user_command: str = ""
    ) -> AgentResponse:
        """Route intent to appropriate agent and return response."""
        logger.debug(
            f"AgentRouter.route_to_agent called with: user_command='{user_command}', intent_type='{intent.type}', intent_entities={intent.entities}"
        )

        try:
            agent_type = self._map_intent_to_agent_type(intent.type)
            agent = self._agents.get(agent_type)

            if agent is None:
                # Fallback: always return GeneralConversationAgent if no agent found
                logger.warning(
                    f"No agent found for type {agent_type.value}, using GeneralConversationAgent as fallback"
                )
                from .general_conversation_agent import \
                    GeneralConversationAgent

                agent = GeneralConversationAgent()

            input_data = self._prepare_agent_input(
                agent_type, user_command, intent, context
            )
            # Ensure 'query' is always set
            input_data["query"] = user_command

            logger.debug(f"Prepared input_data for agent: {input_data}")

            logger.info(f"Routing intent '{intent.type}' to agent {agent_type.value}")
            return await agent.process(input_data)

        except Exception as e:
            logger.error(f"Error routing to agent: {e}", exc_info=True)
            # Even in case of exception, return a fallback response
            try:
                from .general_conversation_agent import \
                    GeneralConversationAgent

                fallback_agent = GeneralConversationAgent()
                input_data = {
                    "query": user_command,
                    "intent": intent.type,
                    "entities": intent.entities,
                    "confidence": intent.confidence,
                    "session_id": context.session_id,
                    "context": context.history[-10:] if context.history else [],
                }
                input_data["query"] = user_command
                return await fallback_agent.process(input_data)
            except Exception as fallback_error:
                logger.error(f"Fallback agent also failed: {fallback_error}")
                return AgentResponse(
                    success=False, error=f"Błąd routingu do agenta: {str(e)}"
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

        # This logic can be expanded for other agents
        return base_data

    def _map_intent_to_agent_type(self, intent_type: str) -> AgentType:
        """Map intent type to agent type"""
        intent_mapping = {
            "cooking": AgentType.CHEF,
            "weather": AgentType.WEATHER,
            "search": AgentType.SEARCH,
            "rag": AgentType.RAG,
            "ocr": AgentType.OCR,
            "categorization": AgentType.CATEGORIZATION,
            "meal_planning": AgentType.MEAL_PLANNER,
            "analytics": AgentType.ANALYTICS,
            "general_conversation": AgentType.GENERAL_CONVERSATION,
        }
        return intent_mapping.get(intent_type, AgentType.GENERAL_CONVERSATION)

    def get_registered_agents(self) -> Dict[AgentType, IBaseAgent]:
        """Get all registered agents"""
        return self._agents.copy()
