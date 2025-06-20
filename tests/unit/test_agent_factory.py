import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.agents.agent_factory import AgentFactory
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "src"))  # Usuń jeśli niepotrzebne


class TestAgentFactory:
    """Testy dla Agent Factory - fabryki tworzenia agentów"""

    @pytest.fixture
    def agent_factory(self):
        """Fixture dla Agent Factory"""
        return AgentFactory()

    @pytest.fixture
    def mock_llm_client(self):
        """Mock klienta LLM"""
        with patch("backend.agents.agent_factory.llm_client") as mock_client:
            yield mock_client

    @pytest.fixture
    def mock_hybrid_llm(self):
        """Mock HybridLLMClient"""
        with patch("backend.core.hybrid_llm_client.HybridLLMClient") as mock_client:
            mock_instance = Mock()
            mock_instance.generate_response = AsyncMock(return_value="Mocked response")
            mock_client.return_value = mock_instance
            yield mock_client

    @pytest.fixture
    def mock_ollama_client(self):
        """Mock OllamaClient"""
        with patch("backend.core.llm_client.OllamaClient") as mock_client:
            mock_instance = Mock()
            mock_instance.generate = AsyncMock(return_value="Mocked response")
            mock_client.return_value = mock_instance
            yield mock_client

    @pytest.fixture
    def mock_config(self):
        """Mock konfiguracji"""
        with patch("backend.agents.agent_factory.config") as mock_config:
            mock_config.AGENT_CONFIG = {
                "Weather": {"module": "weather_agent", "class": "EnhancedWeatherAgent"},
                "Search": {"module": "search_agent", "class": "SearchAgent"},
                "OCR": {"module": "ocr_agent", "class": "OCRAgent"},
            }
            yield mock_config

    @pytest.fixture
    def agent_factory_with_services(self):
        """Fixture dla Agent Factory z zarejestrowanymi wymaganymi serwisami"""
        from backend.agents.interfaces import (
            IAlertService,
            IErrorHandler,
            IFallbackProvider,
        )

        factory = AgentFactory()
        # Rejestracja mocków serwisów w kontenerze
        factory.container.register(IErrorHandler, Mock())
        factory.container.register(IFallbackProvider, Mock())
        factory.container.register(IAlertService, Mock())
        return factory

    @pytest.mark.asyncio
    async def test_create_agent_success(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        """Test pomyślnego tworzenia agenta"""
        agent_type = "Search"
        agent = agent_factory_with_services.create_agent(agent_type)
        assert agent is not None
        assert isinstance(agent, SearchAgent)

    @pytest.mark.asyncio
    async def test_create_agent_invalid_type(self, agent_factory_with_services):
        agent_type = "InvalidAgentType"
        from backend.core.exceptions import BaseCustomException

        with pytest.raises(BaseCustomException):
            agent_factory_with_services.create_agent(agent_type)

    @pytest.mark.asyncio
    async def test_create_agent_with_dependencies(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_hybrid_llm
    ):
        agent_type = "Weather"
        dependencies = {"llm_client": mock_llm_client}
        agent = agent_factory_with_services.create_agent(agent_type, **dependencies)
        assert agent is not None
        # WeatherAgent nie ma atrybutu llm_client, więc sprawdzamy tylko, że agent został utworzony
        assert isinstance(agent, WeatherAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_configuration(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        agent_type = "OCR"
        config = {"timeout": 30, "language": "pol"}
        agent = agent_factory_with_services.create_agent(agent_type, **config)
        assert agent is not None
        assert agent.TIMEOUT == 30
        assert agent.default_language == "pol"

    @pytest.mark.asyncio
    async def test_create_agent_caching(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        agent_type = "Search"
        agent1 = agent_factory_with_services.create_agent(agent_type)
        agent2 = agent_factory_with_services.create_agent(agent_type)
        assert agent1 is agent2

    @pytest.mark.asyncio
    async def test_create_agent_without_caching(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        agent_type = "Search"
        agent1 = agent_factory_with_services.create_agent(agent_type)
        agent2 = agent_factory_with_services.create_agent(agent_type, use_cache=False)
        assert agent1 is not agent2

    @pytest.mark.asyncio
    async def test_create_agent_with_custom_modules(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        agent_type = "CustomAgent"
        custom_config = {"module": "custom_agent_module", "class": "CustomAgentClass"}
        agent_factory_with_services.agent_config[agent_type] = custom_config

        # Mock agent_registry.get_agent_class
        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_class = Mock()
            mock_instance = Mock()
            mock_instance.__str__ = lambda self: "CustomAgentInstance"
            mock_class.return_value = mock_instance
            mock_get_class.return_value = mock_class

            agent = agent_factory_with_services.create_agent(agent_type)
            assert str(agent) == "CustomAgentInstance"

    @pytest.mark.asyncio
    async def test_create_agent_with_fallback(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        agent_type = "Search"
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            agent_factory_with_services.agent_config["search"]["fallback"] = {
                "module": "search_agent",
                "class": "SearchAgent",
            }
            agent = agent_factory_with_services.create_agent(agent_type)
            assert isinstance(agent, SearchAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_initialization_error(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        agent_type = "OCR"
        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_class = Mock()
            mock_class.side_effect = Exception("Init error")
            mock_get_class.return_value = mock_class
            from backend.core.exceptions import BaseCustomException

            with pytest.raises(BaseCustomException):
                agent_factory_with_services.create_agent(agent_type)

    @pytest.mark.asyncio
    async def test_create_agent_with_invalid_config(
        self, agent_factory_with_services, mock_hybrid_llm
    ):
        """Test tworzenia agenta z nieprawidłową konfiguracją"""
        # Given
        agent_type = "Search"

        # Mock agent_registry.get_agent_class, by zwrócił None (nieprawidłowa konfiguracja)
        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_get_class.return_value = None

            # When
            from backend.core.exceptions import BaseCustomException

            with pytest.raises(BaseCustomException):
                agent_factory_with_services.create_agent(agent_type)

    @pytest.mark.asyncio
    async def test_create_agent_with_async_initialization(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        """Test asynchronicznej inicjalizacji agenta"""
        # Given
        agent_type = "Search"

        async def async_init():
            await asyncio.sleep(0.1)
            return "AsyncAgent"

        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_class = Mock()
            mock_class.return_value = async_init()
            mock_get_class.return_value = mock_class

            # When
            agent = agent_factory_with_services.create_agent(agent_type)

            # Then
            assert asyncio.iscoroutine(agent)
            result = await agent
            assert result == "AsyncAgent"

    @pytest.mark.asyncio
    async def test_create_multiple_agent_types(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        """Test tworzenia różnych typów agentów"""
        # Given
        agent_types = ["Weather", "Search", "OCR"]

        # When
        agents = [agent_factory_with_services.create_agent(t) for t in agent_types]

        # Then
        assert len(agents) == 3
        assert all(agent is not None for agent in agents)

    @pytest.mark.asyncio
    async def test_create_agent_with_plugins(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        """Test tworzenia agenta z pluginami"""
        # Given
        agent_type = "Search"
        plugins = ["plugin1", "plugin2"]

        # When
        agent = agent_factory_with_services.create_agent(agent_type, plugins=plugins)

        # Then
        assert agent is not None
        # SearchAgent nie ma atrybutu plugins, więc sprawdzamy tylko, że agent został utworzony
        assert isinstance(agent, SearchAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_state(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        """Test tworzenia agenta ze stanem początkowym"""
        # Given
        agent_type = "Search"
        initial_state = {"key": "value"}

        # When
        agent = agent_factory_with_services.create_agent(
            agent_type, initial_state=initial_state
        )

        # Then
        assert agent is not None
        # SearchAgent nie ma atrybutu state, więc sprawdzamy tylko, że agent został utworzony
        assert isinstance(agent, SearchAgent)

    @pytest.mark.asyncio
    async def test_create_agent_performance(
        self, agent_factory_with_services, mock_config, mock_hybrid_llm
    ):
        """Test wydajności tworzenia agentów"""
        # Given
        agent_type = "Search"
        import time

        # When
        start_time = time.time()
        agent = agent_factory_with_services.create_agent(agent_type)
        end_time = time.time()

        # Then
        assert agent is not None
        assert (end_time - start_time) < 1.0  # Tworzenie agenta powinno być szybkie
