from typing import Any, Dict, Optional

from backend.agents.agent_container import AgentContainer
from backend.agents.base_agent import BaseAgent
from backend.agents.interfaces import IAlertService, IErrorHandler, IFallbackProvider
from backend.core.decorators import handle_exceptions


class AgentBuilder:
    """Builder pattern for configuring and creating agents"""

    def __init__(self, container: AgentContainer, factory: Any = None):
        self.container = container
        self._factory = factory
        self._config: Dict[str, Any] = {}
        self._agent_type: Optional[str] = None

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
