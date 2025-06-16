from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.base_agent import AgentResponse
from backend.agents.orchestrator import Orchestrator


@pytest.fixture
def mock_db_session():
    """Fixture for a mock database session."""
    mock_session = AsyncMock()

    # Configure the mock to handle the chained calls
    mock_result = AsyncMock()
    mock_scalars = AsyncMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    return mock_session


@pytest.mark.asyncio
@patch("backend.agents.orchestrator.AgentFactory")
async def test_orchestrator_routes_to_weather_agent(
    mock_agent_factory, mock_db_session
):
    """
    Tests if the orchestrator correctly routes a weather query to the WeatherAgent.
    """
    # Arrange
    mock_weather_agent = AsyncMock()
    mock_weather_agent.process.return_value = AgentResponse(
        success=True, text="It's sunny."
    )
    mock_agent_factory.return_value.create_agent.return_value = mock_weather_agent

    orchestrator = Orchestrator(mock_db_session)

    # Act
    result = await orchestrator.process_command(
        "jaka jest pogoda w warszawie", "session123"
    )

    # Assert
    mock_agent_factory.return_value.create_agent.assert_called_with("weather")
    mock_weather_agent.process.assert_called_once()
    assert result["response"] == "It's sunny."


@pytest.mark.asyncio
@patch("backend.agents.orchestrator.AgentFactory")
async def test_orchestrator_routes_to_search_agent(mock_agent_factory, mock_db_session):
    """
    Tests if the orchestrator correctly routes a search query to the SearchAgent.
    """
    # Arrange
    mock_search_agent = AsyncMock()
    mock_search_agent.process.return_value = AgentResponse(
        success=True, text="Here are your search results."
    )
    mock_agent_factory.return_value.create_agent.return_value = mock_search_agent

    orchestrator = Orchestrator(mock_db_session)

    # Act
    result = await orchestrator.process_command(
        "wyszukaj informacje o pythonie", "session123"
    )

    # Assert
    mock_agent_factory.return_value.create_agent.assert_called_with("search")
    mock_search_agent.process.assert_called_once()
    assert result["response"] == "Here are your search results."


@pytest.mark.asyncio
@patch("backend.agents.orchestrator.recognize_intent", new_callable=AsyncMock)
@patch("backend.agents.orchestrator.extract_entities", new_callable=AsyncMock)
@patch("backend.agents.orchestrator.execute_database_action", new_callable=AsyncMock)
async def test_orchestrator_handles_database_intent(
    mock_db_action, mock_extract_entities, mock_recognize_intent, mock_db_session
):
    """
    Tests if the orchestrator correctly handles a database-related intent.
    """
    # Arrange
    mock_recognize_intent.return_value = '{"intent": "DODAJ_ZAKUPY"}'
    mock_extract_entities.return_value = (
        '{"produkty": [{"nazwa": "mleko", "cena": 3.5}]}'
    )
    mock_db_action.return_value = True

    orchestrator = Orchestrator(mock_db_session)

    # Act
    result = await orchestrator.process_command("dodaj mleko za 3.5 zł", "session123")

    # Assert
    mock_recognize_intent.assert_called_once()
    mock_extract_entities.assert_called_once()
    mock_db_action.assert_called_once()
    assert "dodałem nowy wpis" in result["response"]
