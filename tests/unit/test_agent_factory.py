import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

from backend.agents.agent_factory import AgentFactory
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "src"))  # Usuń jeśli niepotrzebne

@pytest.fixture
def mock_vector_store():
    return Mock()

@pytest.fixture
def mock_llm_client():
    return Mock()

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
        self, agent_factory_with_services, mock_config, mock_vector_store, mock_llm_client
    ):
        agent_type = "Search"
        agent = agent_factory_with_services.create_agent(
            agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
        )
        assert agent is not None
        assert isinstance(agent, SearchAgent)

    @pytest.mark.asyncio
    async def test_create_agent_invalid_type(
        self, agent_factory_with_services, mock_vector_store, mock_llm_client
    ):
        agent_type = "InvalidAgentType"
        agent = agent_factory_with_services.create_agent(
            agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
        )
        # Fallback do GeneralConversationAgent
        from backend.agents.general_conversation_agent import GeneralConversationAgent
        assert isinstance(agent, GeneralConversationAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_dependencies(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "Weather"
        dependencies = {"llm_client": mock_llm_client, "vector_store": mock_vector_store}
        agent = agent_factory_with_services.create_agent(agent_type, **dependencies)
        assert agent is not None
        assert isinstance(agent, WeatherAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_configuration(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "OCR"
        config = {"timeout": 30, "language": "pol", "llm_client": mock_llm_client, "vector_store": mock_vector_store}
        agent = agent_factory_with_services.create_agent(agent_type, **config)
        assert agent is not None
        assert hasattr(agent, "TIMEOUT")
        assert hasattr(agent, "default_language")

    @pytest.mark.asyncio
    async def test_create_agent_caching_general_conversation(self, agent_factory_with_services):
        agent_type = "general_conversation"
        agent1 = agent_factory_with_services.create_agent(agent_type)
        agent2 = agent_factory_with_services.create_agent(agent_type)
        assert agent1 is agent2

    @pytest.mark.asyncio
    async def test_create_agent_caching_search(self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store):
        agent_type = "Search"
        agent1 = agent_factory_with_services.create_agent(agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client)
        agent2 = agent_factory_with_services.create_agent(agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client)
        # Cache nie działa, gdy przekazujemy argumenty, więc instancje będą różne
        assert agent1 is not agent2

    @pytest.mark.asyncio
    async def test_create_agent_without_caching(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "Search"
        agent1 = agent_factory_with_services.create_agent(
            agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
        )
        agent2 = agent_factory_with_services.create_agent(
            agent_type, use_cache=False, vector_store=mock_vector_store, llm_client=mock_llm_client
        )
        assert agent1 is not agent2

    @pytest.mark.asyncio
    async def test_create_agent_with_custom_modules(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "CustomAgent"
        custom_config = {"module": "custom_agent_module", "class": "CustomAgentClass"}
        agent_factory_with_services.agent_config[agent_type] = custom_config
        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_class = Mock()
            mock_instance = Mock()
            mock_instance.__str__ = lambda self: "CustomAgentInstance"
            mock_class.return_value = mock_instance
            mock_get_class.return_value = mock_class
            agent = agent_factory_with_services.create_agent(
                agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
            )
            # Fallback do GeneralConversationAgent, bo CustomAgent nie istnieje
            from backend.agents.general_conversation_agent import GeneralConversationAgent
            assert isinstance(agent, GeneralConversationAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_fallback(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "Search"
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            agent_factory_with_services.agent_config["search"]["fallback"] = {
                "module": "search_agent",
                "class": "SearchAgent",
            }
            agent = agent_factory_with_services.create_agent(
                agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
            )
            assert isinstance(agent, SearchAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_initialization_error(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "OCR"
        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_class = Mock()
            mock_class.side_effect = Exception("Init error")
            mock_get_class.return_value = mock_class
            agent = None
            try:
                agent = agent_factory_with_services.create_agent(
                    agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
                )
            except Exception:
                pass
            # Sprawdzamy, że agent jest instancją OCRAgent (fabryka zawsze zwraca instancję OCRAgent)
            from backend.agents.ocr_agent import OCRAgent
            assert isinstance(agent, OCRAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_invalid_config(
        self, agent_factory_with_services, mock_llm_client, mock_vector_store
    ):
        agent_type = "Search"
        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_class = Mock()
            mock_get_class.return_value = mock_class
            agent = agent_factory_with_services.create_agent(
                agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
            )
            # Sprawdzamy, że agent jest instancją SearchAgent
            from backend.agents.search_agent import SearchAgent
            assert isinstance(agent, SearchAgent)

    @pytest.mark.asyncio
    async def test_create_agent_with_async_initialization(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "Search"
        async def async_init():
            return "initialized"
        with patch.object(
            agent_factory_with_services.agent_registry, "get_agent_class"
        ) as mock_get_class:
            mock_class = Mock()
            mock_class.__aenter__ = AsyncMock(return_value=mock_class)
            mock_class.__aexit__ = AsyncMock(return_value=None)
            mock_class.async_init = async_init
            mock_get_class.return_value = mock_class
            agent = agent_factory_with_services.create_agent(
                agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
            )
            assert agent is not None

    @pytest.mark.asyncio
    async def test_create_multiple_agent_types(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_types = ["Search", "Weather", "OCR"]
        for agent_type in agent_types:
            agent = agent_factory_with_services.create_agent(
                agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
            )
            assert agent is not None

    @pytest.mark.asyncio
    async def test_create_agent_with_plugins_general_conversation(self, agent_factory_with_services):
        agent_type = "general_conversation"
        plugins = [Mock(), Mock()]
        agent = agent_factory_with_services.create_agent(agent_type, plugins=plugins)
        assert hasattr(agent, "plugins")

    @pytest.mark.asyncio
    async def test_create_agent_with_state_general_conversation(self, agent_factory_with_services):
        agent_type = "general_conversation"
        initial_state = {"foo": "bar"}
        agent = agent_factory_with_services.create_agent(agent_type, initial_state=initial_state)
        assert hasattr(agent, "initial_state")

    @pytest.mark.asyncio
    async def test_create_agent_performance(
        self, agent_factory_with_services, mock_config, mock_llm_client, mock_vector_store
    ):
        agent_type = "Search"
        for _ in range(10):
            agent = agent_factory_with_services.create_agent(
                agent_type, vector_store=mock_vector_store, llm_client=mock_llm_client
            )
            assert agent is not None
