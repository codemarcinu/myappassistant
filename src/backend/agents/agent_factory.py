from typing import Dict, Type

from .analytics_agent import AnalyticsAgent
from .categorization_agent import CategorizationAgent
from .chef_agent import ChefAgent
from .enhanced_base_agent import ImprovedBaseAgent
from .enhanced_orchestrator import EnhancedOrchestrator
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
        "orchestrator": EnhancedOrchestrator,
        # Add additional agent classes here
    }

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
