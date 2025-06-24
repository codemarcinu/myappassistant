import logging
from typing import Any, Dict, Optional

from backend.agents.agent_container import AgentContainer
from backend.agents.base_agent import BaseAgent
from backend.agents.general_conversation_agent import GeneralConversationAgent
from backend.agents.interfaces import (AgentType, IAlertService, IErrorHandler,
                                       IFallbackProvider)
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent
from backend.core.decorators import handle_exceptions
from backend.core.language_detector import language_detector
from backend.core.model_selector import ModelTask, model_selector

logger = logging.getLogger(__name__)


class AgentBuilder:
    """
    Klasa odpowiedzialna za budowanie agentów w oparciu o różne kryteria.
    Wykorzystuje ModelSelector do wyboru odpowiedniego modelu językowego.
    """

    def __init__(self, container: AgentContainer, factory: Any = None) -> None:
        self.container = container
        self._factory = factory
        self._config: Dict[str, Any] = {}
        self._agent_type: Optional[str] = None
        self.agent_classes = {
            AgentType.GENERAL: GeneralConversationAgent,
            AgentType.WEATHER: WeatherAgent,
            AgentType.SEARCH: SearchAgent,
            # ... more agents
        }
        self.model_selector = model_selector
        self.language_detector = language_detector

    def of_type(self, agent_type: str) -> "AgentBuilder":
        """Set the agent type to build"""
        self._agent_type = agent_type
        return self

    def with_config(self, config: Dict[str, Any]) -> "AgentBuilder":
        """Add configuration for the agent"""
        self._config.update(config)
        return self

    @handle_exceptions(max_retries=1)
    def build(self, **kwargs) -> BaseAgent:
        """Build and configure the agent instance"""
        if not self._agent_type:
            raise ValueError("Agent type must be specified")

        # Get core dependencies (optional)
        db = self.container.get("db")
        profile_manager = self.container.get("profile_manager")
        llm_client = self.container.get("llm_client")

        # Create agent with dependencies
        agent = self._create_agent_instance(**kwargs)

        # Inject common dependencies if available
        if hasattr(agent, "set_db") and db:
            agent.set_db(db)
        if hasattr(agent, "set_profile_manager") and profile_manager:
            agent.set_profile_manager(profile_manager)
        if hasattr(agent, "set_llm_client") and llm_client:
            agent.set_llm_client(llm_client)

        # Apply additional configuration
        for key, value in self._config.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        return agent

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    def _create_agent_instance(self, **kwargs) -> BaseAgent:
        """Create the appropriate agent instance"""
        if not self._agent_type:
            raise ValueError("Agent type must be specified")

        # Get agent class from registry
        agent_class = self._factory.agent_registry.get_agent_class(self._agent_type)
        if not agent_class:
            raise ValueError(f"Unsupported agent type: {self._agent_type}")

        # Create agent instance with basic dependencies
        agent_name = f"{self._agent_type}Agent"

        # Get services by interface type (optional)
        error_handler = self.container.get(IErrorHandler)
        fallback_manager = self.container.get(IFallbackProvider)
        alert_service = self.container.get(IAlertService)

        # Create agent with available services
        agent_kwargs = {
            "name": agent_name,
            **kwargs,
        }

        if error_handler:
            agent_kwargs["error_handler"] = error_handler
        if fallback_manager:
            agent_kwargs["fallback_manager"] = fallback_manager
        if alert_service:
            agent_kwargs["alert_service"] = alert_service

        return agent_class(**agent_kwargs)

    def build_agent(
        self,
        agent_type: AgentType,
        query: str = "",
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> BaseAgent:
        """
        Buduje i zwraca odpowiedniego agenta dla podanego typu.
        Jeśli model nie jest określony, wybiera go automatycznie.

        Args:
            agent_type: Typ agenta do zbudowania
            query: Zapytanie użytkownika (do określenia języka)
            context: Kontekst dla agenta
            model: Opcjonalnie określony model

        Returns:
            BaseAgent: Instancja agenta odpowiedniego typu
        """
        if agent_type not in self.agent_classes:
            logger.error(f"Unknown agent type: {agent_type}")
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Jeśli model nie został określony, wybierz automatycznie
        if not model and query:
            # Wykryj język zapytania
            language, _ = self.language_detector.detect_language(query)

            # Wybierz zadanie odpowiednie dla typu agenta
            task = self._map_agent_type_to_task(agent_type)

            # Określ złożoność w zależności od typu agenta
            complexity = self._get_agent_complexity(agent_type)

            # Sprawdź czy zapytanie może zawierać obrazy
            contains_images = self._may_contain_images(query, agent_type)

            # Estymuj długość kontekstu
            context_length = len(query) * 5  # Prosta heurystyka

            # Wybierz model
            model = self.model_selector.select_model(
                query=query,
                task=task,
                complexity=complexity,
                contains_images=contains_images,
                context_length=context_length,
            )

            logger.info(
                f"Selected model {model} for agent {agent_type} "
                f"(lang: {language}, task: {task}, complexity: {complexity:.2f})"
            )

        # Jeśli nadal brak modelu, użyj domyślnego dla danego agenta
        if not model:
            model = self._get_default_model_for_agent(agent_type)

        # Utwórz i zwróć agenta
        agent_class = self.agent_classes[agent_type]
        agent_instance = agent_class()

        # Dodaj model do kontekstu
        if context is None:
            context = {}
        context["model"] = model

        return agent_instance

    def _map_agent_type_to_task(self, agent_type: AgentType) -> ModelTask:
        """Mapuje typ agenta na odpowiedni typ zadania dla modelu"""
        mapping = {
            AgentType.GENERAL: ModelTask.TEXT_ONLY,
            AgentType.WEATHER: ModelTask.TEXT_ONLY,
            AgentType.SEARCH: ModelTask.TEXT_ONLY,
            AgentType.COOKING: ModelTask.CREATIVE,
            AgentType.CODE: ModelTask.CODE_GENERATION,
            AgentType.OCR: ModelTask.IMAGE_ANALYSIS,
            AgentType.CATEGORIZATION: ModelTask.STRUCTURED_OUTPUT,
            AgentType.RAG: ModelTask.RAG,
        }
        return mapping.get(agent_type, ModelTask.TEXT_ONLY)

    def _get_agent_complexity(self, agent_type: AgentType) -> float:
        """Zwraca szacowaną złożoność dla danego typu agenta"""
        complexity_map = {
            AgentType.GENERAL: 0.5,
            AgentType.WEATHER: 0.4,
            AgentType.SEARCH: 0.6,
            AgentType.COOKING: 0.7,
            AgentType.CODE: 0.8,
            AgentType.OCR: 0.9,
            AgentType.CATEGORIZATION: 0.7,
            AgentType.RAG: 0.8,
        }
        return complexity_map.get(agent_type, 0.5)

    def _may_contain_images(self, query: str, agent_type: AgentType) -> bool:
        """
        Sprawdza czy dane zapytanie i typ agenta mogą wymagać analizy obrazów
        """
        # Agenty, które mogą obsługiwać obrazy
        image_capable_agents = {AgentType.OCR, AgentType.SHOPPING}

        # Słowa kluczowe wskazujące na obrazy
        image_keywords = [
            "obraz",
            "zdjęcie",
            "image",
            "photo",
            "picture",
            "scan",
            "screenshot",
            "paragon",
            "receipt",
        ]

        # Sprawdź czy agent jest zdolny do obsługi obrazów
        if agent_type in image_capable_agents:
            return True

        # Sprawdź czy zapytanie zawiera słowa kluczowe związane z obrazami
        return any(keyword in query.lower() for keyword in image_keywords)

    def _get_default_model_for_agent(self, agent_type: AgentType) -> str:
        """Zwraca domyślny model dla danego typu agenta"""
        # Agenty wymagające modelu multimodalnego
        if agent_type in {AgentType.OCR, AgentType.SHOPPING}:
            return "gemma3:12b"

        # Dla pozostałych agentów Bielik jest wystarczający
        return "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
