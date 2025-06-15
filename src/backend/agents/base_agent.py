from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Standardowa odpowiedź agenta"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """Bazowa klasa dla wszystkich agentów"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def process(self, input_data: Any) -> AgentResponse:
        """Główna metoda przetwarzania - musi być zaimplementowana przez każdy agent"""
        pass

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"
