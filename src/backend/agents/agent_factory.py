from typing import Dict, Type

from .analytics_agent import AnalyticsAgent
from .base_agent import BaseAgent
from .categorization_agent import CategorizationAgent
from .chef_agent import ChefAgent
from .enhanced_rag_agent import EnhancedRAGAgent
from .meal_planner_agent import MealPlannerAgent
from .ocr_agent import OCRAgent
from .rag_agent import RAGAgent
from .search_agent import SearchAgent
from .weather_agent import WeatherAgent


class AgentFactory:
    """Fabryka agentów. Pozwala tworzyć agentów na podstawie nazwy."""

    _registry: Dict[str, Type[BaseAgent]] = {
        "ocr": OCRAgent,
        "weather": WeatherAgent,
        "search": SearchAgent,
        "chef": ChefAgent,
        "meal_planner": MealPlannerAgent,
        "categorization": CategorizationAgent,
        "analytics": AnalyticsAgent,
        "rag": RAGAgent,
        "enhanced_rag": EnhancedRAGAgent,
        # Dodaj tu kolejne klasy agentów, np. "parser": ParserAgent
    }

    @classmethod
    def create_agent(cls, agent_type: str) -> BaseAgent:
        """
        Tworzy instancję agenta na podstawie typu.

        Args:
            agent_type (str): Typ agenta (np. 'ocr')

        Returns:
            BaseAgent: Instancja agenta

        Raises:
            ValueError: Jeśli nie znaleziono agenta o podanym typie.
        """
        if agent_type not in cls._registry:
            raise ValueError(f"Nieznany typ agenta: {agent_type}")
        agent_class = cls._registry[agent_type]
        agent_name = f"{agent_type}_agent"
        if not isinstance(agent_name, str):
            agent_name = str(agent_name)
        return agent_class(name=agent_name)
