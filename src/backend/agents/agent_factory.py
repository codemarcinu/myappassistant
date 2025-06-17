from typing import Dict, Type

from .analytics_agent import AnalyticsAgent
from .categorization_agent import CategorizationAgent
from .chef_agent import ChefAgent
from .enhanced_base_agent import ImprovedBaseAgent

# Removed import of EnhancedOrchestrator to avoid circular dependency
from .enhanced_rag_agent import EnhancedRAGAgent
from .enhanced_weather_agent import EnhancedWeatherAgent
from .meal_planner_agent import MealPlannerAgent
from .ocr_agent import OCRAgent
from .search_agent import SearchAgent


class AgentFactory:
    """Factory for creating agent instances based on type."""

    _registry: Dict[str, Type[ImprovedBaseAgent]] = {
        "ocr": OCRAgent,
        "weather": EnhancedWeatherAgent,
        "search": SearchAgent,
        "chef": ChefAgent,
        "meal_planner": MealPlannerAgent,
        "categorization": CategorizationAgent,
        "analytics": AnalyticsAgent,
        "rag": EnhancedRAGAgent,
        # Removed EnhancedOrchestrator to avoid circular dependency
        # Add additional agent classes here
    }

    @classmethod
    def register_agent(cls, agent_type: str, agent_instance: ImprovedBaseAgent) -> None:
        """
        Register an agent instance with the factory.
        This method allows for runtime registration of agents.

        Args:
            agent_type (str): Type of agent (e.g., 'enhanced_orchestrator')
            agent_instance (ImprovedBaseAgent): Instance of the agent
        """
        cls._registry[agent_type] = agent_instance.__class__

    @classmethod
    def create_agent(cls, agent_type: str) -> ImprovedBaseAgent:
        """
        Creates an agent instance based on the specified type.

        Args:
            agent_type (str): Type of agent (e.g., 'ocr', 'weather')

        Returns:
            ImprovedBaseAgent: Instance of the requested agent

        Raises:
            ValueError: If the agent type is not found in the registry.
        """
        if agent_type not in cls._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = cls._registry[agent_type]
        agent_name = f"{agent_type}_agent"
        if not isinstance(agent_name, str):
            agent_name = str(agent_name)

        return agent_class(name=agent_name)
