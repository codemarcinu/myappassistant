import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

# Prosta konfiguracja logowania, aby widzieć co się dzieje w konsoli
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AgentResponse(BaseModel):
    """
    Ustandaryzowany format odpowiedzi, który będzie zwracany przez każdego agenta.
    Dzięki temu Orchestrator będzie wiedział, czego się spodziewać.
    """
    success: bool
    result: Any
    error: Optional[str] = None

class BaseAgent(ABC):
    """
    Abstrakcyjna klasa bazowa, która definiuje wspólny interfejs dla wszystkich agentów.
    Każdy nowy agent (np. CodeAgent, FoodSaveAgent) będzie po niej dziedziczył.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{self.name}")
        self.logger.info(f"Agent '{self.name}' został zainicjalizowany.")

    @abstractmethod
    async def execute(self, task_description: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Główna metoda, którą KAŻDY agent będzie musiał zaimplementować.
        To tutaj będzie dziać się cała 'magia' i logika danego agenta.

        Args:
            task_description: Opis zadania do wykonania, np. "napisz funkcję sortującą".
            context: Opcjonalny słownik z dodatkowymi danymi (np. kodem z otwartego pliku).

        Returns:
            Obiekt AgentResponse z wynikiem operacji.
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """Zwraca podstawowe informacje o agencie."""
        return {
            "name": self.name,
            "description": self.description
        }