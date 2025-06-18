import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.core.hybrid_llm_client import ModelComplexity, hybrid_llm_client

from ..agents.enhanced_base_agent import EnhancedAgentResponse
from ..agents.enhanced_weather_agent import EnhancedWeatherAgent

logger = logging.getLogger(__name__)


class IntentionHandler(ABC):
    """Base class for intention handlers in Chain of Responsibility"""

    def __init__(self, next_handler: Optional["IntentionHandler"] = None):
        self.next_handler = next_handler

    @abstractmethod
    async def handle(
        self,
        command: str,
        intent_data: Dict[str, Any],
        session_id: str,
        complexity_level: ModelComplexity,
        agent_states: Dict[str, bool],
        **kwargs,
    ) -> Optional[EnhancedAgentResponse]:
        pass


class RouterService:
    """Service for routing commands to appropriate agents"""

    def __init__(self):
        self.handlers = self._initialize_handlers()

    def _initialize_handlers(self) -> IntentionHandler:
        """Initialize Chain of Responsibility for intention handlers"""
        # Initialize just the weather handler for now
        weather_handler = WeatherHandler(EnhancedWeatherAgent())
        return weather_handler

    async def detect_intent(
        self,
        command: str,
        personalized_context: str = "",
        memory_context: str = "",
        complexity_level: ModelComplexity = ModelComplexity.STANDARD,
    ) -> Dict[str, Any]:
        """Detect user intent with context awareness"""
        # Construct prompt with available context
        context_parts = []
        if personalized_context:
            context_parts.append(personalized_context)
        if memory_context:
            context_parts.append(memory_context)

        context_text = "\n\n".join(context_parts)

        prompt = f"""Przeanalizuj intencję użytkownika w poniższym zapytaniu:

Zapytanie: "{command}"

{context_text}

Określ główną intencję z poniższych kategorii:
- WEATHER: Zapytanie o pogodę lub warunki atmosferyczne
- SEARCH: Ogólne wyszukiwanie informacji
- RAG: Zapytanie o wiedzę zgromadzoną w dokumentach
- COOKING: Zapytanie związane z gotowaniem, przepisami lub planowaniem posiłków
- SHOPPING: Zapytanie związane z zakupami lub zarządzaniem produktami
- CHAT: Konwersacja ogólna lub small talk
- UNKNOWN: Intencja nie pasuje do żadnej z powyższych kategorii

Odpowiedz w formacie JSON:
{{
  "intent": "NAZWA_INTENCJI",
  "confidence": 0.0-1.0,
  "entities": [],
  "requires_clarification": false
}}
"""

        # Select model based on complexity
        model = (
            "gemma2:2b" if complexity_level == ModelComplexity.SIMPLE else "gemma3:12b"
        )

        response = await hybrid_llm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś asystentem analizującym intencje użytkownika.",
                },
                {"role": "user", "content": prompt},
            ],
            model=model,
            force_complexity=complexity_level,
        )

        # Extract JSON from response
        if response and "message" in response:
            content = response["message"]["content"]

            # Find JSON content (simple implementation)
            import json
            import re

            json_match = re.search(r"({.*})", content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(1).strip()
                    return json.loads(json_str)
                except (json.JSONDecodeError, IndexError) as e:
                    logger.error(f"Error parsing intent JSON: {e}")

        # Fallback if parsing fails
        return {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "entities": [],
            "requires_clarification": False,
        }

    async def route_command(
        self,
        command: str,
        intent_data: Dict[str, Any],
        session_id: str,
        complexity_level: ModelComplexity,
        agent_states: Dict[str, bool],
        **kwargs,
    ) -> EnhancedAgentResponse:
        """Route command using Chain of Responsibility"""
        return await self.handlers.handle(
            command=command,
            intent_data=intent_data,
            session_id=session_id,
            complexity_level=complexity_level,
            agent_states=agent_states,
            **kwargs,
        )


class WeatherHandler(IntentionHandler):
    def __init__(self, weather_agent: EnhancedWeatherAgent, next_handler=None):
        super().__init__(next_handler)
        self.weather_agent = weather_agent

    async def handle(
        self,
        command: str,
        intent_data: Dict[str, Any],
        session_id: str,
        complexity_level: ModelComplexity,
        agent_states: Dict[str, bool],
        **kwargs,
    ) -> Optional[EnhancedAgentResponse]:
        if intent_data.get("intent") == "WEATHER" and agent_states.get("weather", True):
            return await self.weather_agent.process(
                {"query": command, "model": "gemma3:12b", "include_alerts": True}
            )
        if self.next_handler:
            return await self.next_handler.handle(
                command,
                intent_data,
                session_id,
                complexity_level,
                agent_states,
                **kwargs,
            )
        return None
