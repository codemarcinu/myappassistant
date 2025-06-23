from typing import Dict, List, Optional

from backend.agents.base_agent import BaseAgent
from backend.agents.plugin_interface import AgentPlugin


class PluginManager:
    """Manages registration and execution of agent plugins"""

    def __init__(self) -> None:
        self.plugins: Dict[str, AgentPlugin] = {}

    def register_plugin(self, name: str, plugin: AgentPlugin) -> None:
        """Register a new plugin

        Args:
            name: Unique plugin identifier
            plugin: Plugin instance implementing AgentPlugin
        """
        if name in self.plugins:
            raise ValueError(f"Plugin {name} already registered")
        self.plugins[name] = plugin

    def unregister_plugin(self, name: str) -> None:
        """Remove a registered plugin

        Args:
            name: Plugin identifier to remove
        """
        self.plugins.pop(name, None)

    def initialize_plugins(self, agent: BaseAgent) -> None:
        """Initialize all plugins with agent instance"""
        for plugin in self.plugins.values():
            plugin.initialize(agent)

    def apply_before_processing(self, input_data: Dict) -> Dict:
        """Apply all before_process hooks"""
        result = input_data
        for plugin in self.plugins.values():
            result = plugin.before_process(result)
        return result

    def apply_after_processing(self, output_data: Dict) -> Dict:
        """Apply all after_process hooks"""
        result = output_data
        for plugin in self.plugins.values():
            result = plugin.after_process(result)
        return result

    def get_plugin(self, name: str) -> Optional[AgentPlugin]:
        """Get registered plugin by name"""
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        """Get names of all registered plugins"""
        return list(self.plugins.keys())
