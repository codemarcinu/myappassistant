from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from backend.agents.plugin_interface import AgentPlugin
from backend.agents.plugin_manager import PluginManager


class TestPlugin(AgentPlugin):
    def initialize(self, agent: Any) -> None:
        self.agent = agent

    def before_process(self, input_data: Any) -> Any:
        input_data["processed"] = True
        return input_data

    def after_process(self, output_data: Any) -> Any:
        output_data["post_processed"] = True
        return output_data

    def get_metadata(self) -> dict[str, Any]:
        return {"version": "1.0"}


@pytest.fixture
def plugin_manager() -> PluginManager:
    return PluginManager()


@pytest.fixture
def test_plugin() -> TestPlugin:
    return TestPlugin()


def test_register_plugin(
    plugin_manager: PluginManager, test_plugin: TestPlugin
) -> None:
    plugin_manager.register_plugin("test", test_plugin)
    assert "test" in plugin_manager.list_plugins()


def test_duplicate_registration(
    plugin_manager: PluginManager, test_plugin: TestPlugin
) -> None:
    plugin_manager.register_plugin("test", test_plugin)
    with pytest.raises(ValueError):
        plugin_manager.register_plugin("test", test_plugin)


def test_unregister_plugin(
    plugin_manager: PluginManager, test_plugin: TestPlugin
) -> None:
    plugin_manager.register_plugin("test", test_plugin)
    plugin_manager.unregister_plugin("test")
    assert "test" not in plugin_manager.list_plugins()


def test_initialize_plugins(
    plugin_manager: PluginManager, test_plugin: TestPlugin
) -> None:
    mock_agent = MagicMock()
    plugin_manager.register_plugin("test", test_plugin)
    plugin_manager.initialize_plugins(mock_agent)
    assert test_plugin.agent == mock_agent


def test_before_processing(
    plugin_manager: PluginManager, test_plugin: TestPlugin
) -> None:
    plugin_manager.register_plugin("test", test_plugin)
    result = plugin_manager.apply_before_processing({"data": "test"})
    assert result["processed"] is True


def test_after_processing(
    plugin_manager: PluginManager, test_plugin: TestPlugin
) -> None:
    plugin_manager.register_plugin("test", test_plugin)
    result = plugin_manager.apply_after_processing({"data": "test"})
    assert result["post_processed"] is True


def test_get_plugin(plugin_manager: PluginManager, test_plugin: TestPlugin) -> None:
    plugin_manager.register_plugin("test", test_plugin)
    assert plugin_manager.get_plugin("test") == test_plugin
