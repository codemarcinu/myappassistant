from typing import Dict, Type

from .base_agent import BaseAgent
from .ocr_agent import OCRAgent


class AgentFactory:
    """Fabryka agentów. Pozwala tworzyć agentów na podstawie nazwy."""

    _registry: Dict[str, Type[BaseAgent]] = {
        "ocr": OCRAgent,
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
        return agent_class(name="")
