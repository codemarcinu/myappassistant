from typing import Dict, Optional, Type

from .agent_builder import AgentBuilder
from .agent_container import AgentContainer
from .enhanced_base_agent import ImprovedBaseAgent


class AgentFactory:
    """Factory for creating agent instances with DI support."""

    def __init__(self, container: Optional[AgentContainer] = None):
        self.container = container or AgentContainer()
        self._registry: Dict[str, Type[ImprovedBaseAgent]] = {
            "ocr": self._get_agent_class("OCRAgent"),
            "weather": self._get_agent_class("EnhancedWeatherAgent"),
            "search": self._get_agent_class("SearchAgent"),
            "chef": self._get_agent_class("ChefAgent"),
            "meal_planner": self._get_agent_class("MealPlannerAgent"),
            "categorization": self._get_agent_class("CategorizationAgent"),
            "analytics": self._get_agent_class("AnalyticsAgent"),
            "rag": self._get_agent_class("EnhancedRAGAgent"),
        }

    def register_agent(
        self, agent_type: str, agent_class: Type[ImprovedBaseAgent]
    ) -> None:
        """
        Register an agent class with the factory.

        Args:
            agent_type (str): Type of agent (e.g., 'enhanced_orchestrator')
            agent_class (Type[ImprovedBaseAgent]): Agent class to register
        """
        self._registry[agent_type] = agent_class

    def create_agent(
        self, agent_type: str, config: Optional[Dict] = None
    ) -> ImprovedBaseAgent:
        """
        Creates and configures an agent instance using AgentBuilder.

        Args:
            agent_type (str): Type of agent (e.g., 'ocr', 'weather')
            config (Optional[Dict]): Additional configuration for the agent

        Returns:
            ImprovedBaseAgent: Configured agent instance

        Raises:
            ValueError: If the agent type is not found in the registry.
        """
        if agent_type not in self._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")

        builder = AgentBuilder(self.container)
        builder.of_type(agent_type)

        if config:
            builder.with_config(config)

        return builder.build()

    def _get_agent_class(self, class_name: str) -> Type[ImprovedBaseAgent]:
        """Dynamically import agent class to avoid circular imports"""
        module = __import__(
            f"src.backend.agents.{class_name.lower()}", fromlist=[class_name]
        )
        return getattr(module, class_name)
