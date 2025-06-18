from typing import Any, Dict, Optional

from .agent_container import AgentContainer
from .enhanced_base_agent import ImprovedBaseAgent


class AgentBuilder:
    """Builder pattern for configuring and creating agents"""

    def __init__(self, container: AgentContainer):
        self.container = container
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

    def build(self) -> ImprovedBaseAgent:
        """Build and configure the agent instance"""
        if not self._agent_type:
            raise ValueError("Agent type must be specified")

        # Get core dependencies
        db = self.container.get("db")
        profile_manager = self.container.get("profile_manager")
        llm_client = self.container.get("llm_client")

        # Create agent with dependencies
        agent = self._create_agent_instance()

        # Inject common dependencies
        if hasattr(agent, "set_db"):
            agent.set_db(db)
        if hasattr(agent, "set_profile_manager"):
            agent.set_profile_manager(profile_manager)
        if hasattr(agent, "set_llm_client"):
            agent.set_llm_client(llm_client)

        # Apply additional configuration
        for key, value in self._config.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        return agent

    def _create_agent_instance(self) -> ImprovedBaseAgent:
        """Create the appropriate agent instance"""
        from .agent_factory import AgentFactory

        return AgentFactory.create_agent(self._agent_type)
