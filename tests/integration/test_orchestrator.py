from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.orchestration_components import IntentData, MemoryContext
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


@pytest.fixture
def mock_profile_manager():
    """Fixture for a mock profile manager."""
    mock_pm = AsyncMock()
    mock_pm.get_or_create_profile.return_value = None
    mock_pm.log_activity.return_value = None
    return mock_pm


@pytest.fixture
def mock_intent_detector():
    """Fixture for a mock intent detector."""
    mock_detector = AsyncMock()
    return mock_detector


@pytest.fixture
def mock_agent_router():
    """Fixture for a mock agent router."""
    mock_router = AsyncMock()
    return mock_router


@pytest.fixture
def mock_memory_manager():
    """Fixture for a mock memory manager."""
    mock_mm = AsyncMock()
    mock_context = MemoryContext("test_session")
    mock_mm.get_context.return_value = mock_context
    mock_mm.update_context.return_value = None
    return mock_mm


@pytest.fixture
def mock_response_generator():
    """Fixture for a mock response generator."""
    mock_rg = AsyncMock()
    return mock_rg


@pytest.mark.asyncio
async def test_orchestrator_routes_to_weather_agent(
    mock_db_session,
    mock_profile_manager,
    mock_intent_detector,
    mock_agent_router,
    mock_memory_manager,
    mock_response_generator,
):
    """
    Tests if the orchestrator correctly routes a weather query to the WeatherAgent.
    """
    # Arrange
    mock_intent = IntentData(type="weather_query", confidence=0.9)
    mock_intent_detector.detect_intent.return_value = mock_intent

    mock_agent_response = AgentResponse(
        success=True,
        text="It's sunny.",
        data={"temperature": "25°C", "condition": "sunny"},
    )
    mock_agent_router.route_to_agent.return_value = mock_agent_response

    orchestrator = Orchestrator(
        db_session=mock_db_session,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator,
    )

    # Act
    result = await orchestrator.process_command(
        "jaka jest pogoda w warszawie", "session123"
    )

    # Assert
    assert result.success is True
    assert result.text == "It's sunny."
    mock_profile_manager.get_or_create_profile.assert_called_once_with("session123")
    mock_profile_manager.log_activity.assert_called_once()
    mock_intent_detector.detect_intent.assert_called_once()
    mock_agent_router.route_to_agent.assert_called_once()
    mock_memory_manager.update_context.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_routes_to_search_agent(
    mock_db_session,
    mock_profile_manager,
    mock_intent_detector,
    mock_agent_router,
    mock_memory_manager,
    mock_response_generator,
):
    """
    Tests if the orchestrator correctly routes a search query to the SearchAgent.
    """
    # Arrange
    mock_intent = IntentData(type="document_query", confidence=0.9)
    mock_intent_detector.detect_intent.return_value = mock_intent

    mock_agent_response = AgentResponse(
        success=True,
        text="Here are your search results.",
        data={"results": ["result1", "result2"]},
    )
    mock_agent_router.route_to_agent.return_value = mock_agent_response

    orchestrator = Orchestrator(
        db_session=mock_db_session,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator,
    )

    # Act
    result = await orchestrator.process_command(
        "wyszukaj informacje o pythonie", "session123"
    )

    # Assert
    assert result.success is True
    assert result.text == "Here are your search results."
    mock_profile_manager.get_or_create_profile.assert_called_once_with("session123")
    mock_profile_manager.log_activity.assert_called_once()
    mock_intent_detector.detect_intent.assert_called_once()
    mock_agent_router.route_to_agent.assert_called_once()
    mock_memory_manager.update_context.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_handles_circuit_breaker_error(
    mock_db_session,
    mock_profile_manager,
    mock_intent_detector,
    mock_agent_router,
    mock_memory_manager,
    mock_response_generator,
):
    """
    Tests if the orchestrator handles circuit breaker errors gracefully.
    """
    # Arrange
    mock_intent = IntentData(type="recipe_request", confidence=0.9)
    mock_intent_detector.detect_intent.return_value = mock_intent

    # Simulate circuit breaker error
    import pybreaker

    mock_agent_router.route_to_agent.side_effect = pybreaker.CircuitBreakerError()

    orchestrator = Orchestrator(
        db_session=mock_db_session,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator,
    )

    # Act
    result = await orchestrator.process_command(
        "pokaż mi przepis na spaghetti", "session123"
    )

    # Assert
    assert result.success is False
    assert "Service temporarily unavailable" in result.error
    mock_profile_manager.get_or_create_profile.assert_called_once_with("session123")
    mock_profile_manager.log_activity.assert_called_once()
    mock_intent_detector.detect_intent.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_handles_general_exception(
    mock_db_session,
    mock_profile_manager,
    mock_intent_detector,
    mock_agent_router,
    mock_memory_manager,
    mock_response_generator,
):
    """
    Tests if the orchestrator handles general exceptions gracefully.
    """
    # Arrange
    mock_intent_detector.detect_intent.side_effect = Exception("Test error")

    orchestrator = Orchestrator(
        db_session=mock_db_session,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator,
    )

    # Act
    result = await orchestrator.process_command("test command", "session123")

    # Assert
    assert result.success is False
    assert "An error occurred" in result.error
    mock_profile_manager.get_or_create_profile.assert_called_once_with("session123")


@pytest.mark.asyncio
async def test_orchestrator_health_check(
    mock_db_session,
    mock_profile_manager,
    mock_intent_detector,
    mock_agent_router,
    mock_memory_manager,
    mock_response_generator,
):
    """
    Tests if the orchestrator responds to health check commands.
    """
    # Arrange
    orchestrator = Orchestrator(
        db_session=mock_db_session,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator,
    )

    # Act
    result = await orchestrator.process_command("health_check_internal", "session123")

    # Assert
    assert result.success is True
    assert result.data["status"] == "ok"
    assert result.data["message"] == "Orchestrator is responsive"
    # Should not call other components for health check
    mock_profile_manager.get_or_create_profile.assert_not_called()
    mock_intent_detector.detect_intent.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_process_file(
    mock_db_session,
    mock_profile_manager,
    mock_intent_detector,
    mock_agent_router,
    mock_memory_manager,
    mock_response_generator,
):
    """
    Tests if the orchestrator correctly processes uploaded files.
    """
    # Arrange
    mock_agent_response = AgentResponse(
        success=True,
        text="File processed successfully.",
        data={"extracted_text": "Sample text from image"},
    )
    mock_agent_router.route_to_agent.return_value = mock_agent_response

    orchestrator = Orchestrator(
        db_session=mock_db_session,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator,
    )

    # Act
    result = await orchestrator.process_file(
        file_bytes=b"fake_image_data",
        filename="test_image.jpg",
        session_id="session123",
        content_type="image/jpeg",
    )

    # Assert
    assert result.success is True
    assert result.text == "File processed successfully."
    mock_profile_manager.get_or_create_profile.assert_called_once_with("session123")
    mock_profile_manager.log_activity.assert_called_once()
    mock_agent_router.route_to_agent.assert_called_once()
    mock_memory_manager.update_context.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_process_file_unsupported_type(
    mock_db_session,
    mock_profile_manager,
    mock_intent_detector,
    mock_agent_router,
    mock_memory_manager,
    mock_response_generator,
):
    """
    Tests if the orchestrator handles unsupported file types correctly.
    """
    # Arrange
    orchestrator = Orchestrator(
        db_session=mock_db_session,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator,
    )

    # Act
    result = await orchestrator.process_file(
        file_bytes=b"fake_data",
        filename="test.txt",
        session_id="session123",
        content_type="text/plain",
    )

    # Assert
    assert result.success is False
    assert "Unsupported content type" in result.error
    mock_profile_manager.get_or_create_profile.assert_called_once_with("session123")
    mock_profile_manager.log_activity.assert_called_once()
    # Should not call agent router for unsupported types
    mock_agent_router.route_to_agent.assert_not_called()
