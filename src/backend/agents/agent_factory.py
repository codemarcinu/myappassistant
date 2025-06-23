import logging
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from backend.agents.agent_builder import AgentBuilder
from backend.agents.agent_container import AgentContainer
from backend.agents.agent_registry import AgentRegistry
from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.base_agent import BaseAgent
from backend.agents.categorization_agent import CategorizationAgent
from backend.agents.chef_agent import ChefAgent
from backend.agents.general_conversation_agent import GeneralConversationAgent
from backend.agents.meal_planner_agent import MealPlannerAgent
from backend.agents.ocr_agent import OCRAgent
from backend.agents.rag_agent import RAGAgent
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent
from backend.core.decorators import handle_exceptions

# Module-level configuration
config: Dict[str, Any] = {}
llm_client: Optional[Any] = None

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Basic configuration model for agents"""

    agent_type: str
    dependencies: Dict[str, str] = {}
    settings: Dict[str, Any] = {}
    cache_enabled: bool = True


class AgentFactory:
    """Factory for creating agent instances with DI support."""

    def __init__(
        self,
        container: Optional[AgentContainer] = None,
        agent_registry: Optional[AgentRegistry] = None,
    ) -> None:
        self.container = container or AgentContainer()
        self.config: Dict[str, Any] = {}
        self._agent_cache: Dict[str, BaseAgent] = {}  # Cache dla agentów
        self._registry: Dict[str, BaseAgent] = {}  # Registry dla agentów (dla testów)
        self.agent_config = {
            "ocr": {"module": "ocr_agent"},
            "weather": {"module": "weather_agent"},
            "search": {"module": "search_agent"},
            "chef": {"module": "chef_agent"},
            "meal_planner": {"module": "meal_planner_agent"},
            "categorization": {"module": "categorization_agent"},
            "analytics": {"module": "analytics_agent"},
            "rag": {"module": "rag_agent"},
            "orchestrator": {"module": "orchestrator"},
        }
        self.agent_registry = agent_registry or AgentRegistry()

        # Register core services in container
        if hasattr(self.container, "register_core_services"):
            # We need a db session, but we don't have one here
            # This will be handled when creating agents
            pass

        # Register agent classes with the registry
        general_conversation_cls = self._get_agent_class("GeneralConversationAgent")
        self.agent_registry.register_agent_class(
            "GeneralConversation", general_conversation_cls
        )
        self.agent_registry.register_agent_class(
            "GeneralConversationAgent", general_conversation_cls
        )
        self.agent_registry.register_agent_class(
            "OCR", self._get_agent_class("OCRAgent")
        )
        self.agent_registry.register_agent_class(
            "Weather", self._get_agent_class("WeatherAgent")
        )
        self.agent_registry.register_agent_class(
            "Search", self._get_agent_class("SearchAgent")
        )
        self.agent_registry.register_agent_class(
            "Chef", self._get_agent_class("ChefAgent")
        )
        self.agent_registry.register_agent_class(
            "MealPlanner", self._get_agent_class("MealPlannerAgent")
        )
        self.agent_registry.register_agent_class(
            "Categorization", self._get_agent_class("CategorizationAgent")
        )
        self.agent_registry.register_agent_class(
            "Analytics", self._get_agent_class("AnalyticsAgent")
        )
        self.agent_registry.register_agent_class(
            "RAG", self._get_agent_class("RAGAgent")
        )
        self.agent_registry.register_agent_class(
            "CustomAgent", self._get_agent_class("BaseAgent")
        )

    def register_agent(self, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class with the factory and registry.

        Args:
            agent_type (str): Type of agent (e.g., 'orchestrator')
            agent_class (Type[BaseAgent]): Agent class to register
        """
        self.agent_registry.register_agent_class(agent_type, agent_class)

    @handle_exceptions(max_retries=1)
    def create_agent(
        self,
        agent_type: str,
        config: Optional[Dict] = None,
        use_cache: bool = True,
        **kwargs,
    ) -> BaseAgent:
        """
        Creates and configures an agent instance using AgentBuilder.

        Args:
            agent_type (str): Type of agent (e.g., 'ocr', 'weather')
            config (Optional[Dict]): Additional configuration for the agent
            use_cache (bool): Whether to use cached agent instance
            **kwargs: Additional arguments to pass to agent constructor

        Returns:
            BaseAgent: Configured agent instance

        Raises:
            ValueError: If the agent type is not found in the registry.
        """
        # Sprawdź cache jeśli włączony
        if use_cache and not config and not kwargs:
            cache_key = agent_type
            if cache_key in self._agent_cache:
                return self._agent_cache[cache_key]

        # Map agent_type to registered agent class using intent_to_agent_mapping
        mapped_agent_type = self.agent_registry.intent_to_agent_mapping.get(agent_type, "GeneralConversation")
        agent_class = self.agent_registry.get_agent_class(mapped_agent_type)
        if not agent_class:
            # Fallback: always return GeneralConversationAgent if mapping fails
            from backend.agents.general_conversation_agent import GeneralConversationAgent
            logger.warning(
                f"Unknown agent type: {agent_type} (mapped: {mapped_agent_type}), using GeneralConversationAgent as fallback"
            )
            return GeneralConversationAgent()

        builder = AgentBuilder(self.container, self)
        builder.of_type(agent_type)

        if config:
            builder.with_config(config)

        agent = builder.build(**kwargs)

        # Zapisz w cache jeśli włączony i nie ma dodatkowej konfiguracji
        if use_cache and not config and not kwargs:
            cache_key = agent_type
            self._agent_cache[cache_key] = agent

        return agent

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    def _get_agent_class(self, class_name: str) -> Type[BaseAgent]:
        """Dynamically import agent class to avoid circular imports"""
        import importlib
        import os
        import sys

        # Get the project root path (relative to this file)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Map class names to actual module files (relative imports)
        module_map = {
            "GeneralConversationAgent": "general_conversation_agent",
            "OCRAgent": "ocr_agent",
            "WeatherAgent": "weather_agent",
            "SearchAgent": "search_agent",
            "ChefAgent": "chef_agent",
            "MealPlannerAgent": "meal_planner_agent",
            "CategorizationAgent": "categorization_agent",
            "AnalyticsAgent": "analytics_agent",
            "RAGAgent": "rag_agent",
            "Orchestrator": "orchestrator",
            "BaseAgent": "base_agent",
        }

        if class_name not in module_map:
            raise ValueError(f"No module mapping for agent class: {class_name}")

        module_name = module_map[class_name]
        full_module_path = f"backend.agents.{module_name}"

        try:
            module = importlib.import_module(full_module_path)
            return getattr(module, class_name)
        except ImportError as e:
            # Check if file actually exists
            file_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
            if not os.path.exists(file_path):
                raise FileNotFoundError(
                    f"Agent module file not found: {file_path}"
                ) from e
            else:
                raise ImportError(
                    f"Failed to import {class_name} from {full_module_path}: {str(e)}\n"
                    f"Current sys.path: {sys.path}"
                ) from e

    def get_available_agents(self) -> Dict[str, str]:
        """Return a dictionary of available agent types and their descriptions"""
        return {
            "general_conversation": "Agent do swobodnych konwersacji z RAG i wyszukiwaniem",
            "chef": "Agent do przepisów kulinarnych",
            "weather": "Agent do prognoz pogody",
            "search": "Agent do wyszukiwania w internecie",
            "rag": "Agent do analizy dokumentów",
            "ocr": "Agent do analizy obrazów i paragonów",
            "categorization": "Agent do kategoryzacji produktów",
            "meal_planner": "Agent do planowania posiłków",
            "analytics": "Agent do analizy danych",
        }

    def cleanup(self) -> None:
        """Clear the agent cache and registry"""
        self._agent_cache.clear()
        self._registry.clear()

    def reset(self) -> None:
        """Reset the factory to initial state"""
        self.cleanup()
        self.config.clear()
