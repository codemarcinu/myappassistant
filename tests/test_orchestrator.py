import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.interfaces import AgentResponse
from backend.agents.orchestrator import Orchestrator
from backend.agents.agent_router import AgentRouter
from backend.agents.intent_detector import SimpleIntentDetector
from backend.agents.memory_manager import MemoryManager
from backend.agents.response_generator import ResponseGenerator
from backend.core.profile_manager import ProfileManager


@pytest.mark.asyncio
async def test_orchestrator_process_query():
    """Test podstawowej funkcji przetwarzania zapytania przez orchestrator"""
    # Przygotowanie mocków
    mock_db = MagicMock()
    mock_profile_manager = MagicMock(spec=ProfileManager)
    mock_profile_manager.get_or_create_profile = AsyncMock(return_value={"id": "test_user"})
    mock_profile_manager.log_activity = AsyncMock()
    
    mock_intent_detector = MagicMock(spec=SimpleIntentDetector)
    mock_intent_detector.detect_intent = AsyncMock(return_value="weather")
    
    mock_agent_router = MagicMock(spec=AgentRouter)
    mock_agent_router.route = AsyncMock(return_value=MagicMock())
    
    mock_memory_manager = MagicMock(spec=MemoryManager)
    mock_memory_manager.get_context = AsyncMock(return_value={})
    mock_memory_manager.update_context = AsyncMock()
    
    mock_response_generator = MagicMock(spec=ResponseGenerator)
    mock_response_generator.generate = AsyncMock(
        return_value=AgentResponse(
            success=True,
            text="Pogoda w Warszawie jest słoneczna.",
            message="Pogoda w Warszawie jest słoneczna."
        )
    )
    
    # Tworzenie orchestratora z mockami
    orchestrator = Orchestrator(
        db_session=mock_db,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator
    )
    
    # Wywołanie metody process_query
    query = "Jaka jest pogoda w Warszawie?"
    session_id = "test_session"
    result = await orchestrator.process_query(query, session_id)
    
    # Weryfikacja
    assert result.success is True
    assert "Pogoda w Warszawie" in result.text
    
    # Sprawdzenie czy odpowiednie metody zostały wywołane
    mock_profile_manager.get_or_create_profile.assert_called_once_with(session_id)
    mock_memory_manager.get_context.assert_called_once()
    mock_intent_detector.detect_intent.assert_called_once()
    mock_agent_router.route.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_process_file():
    """Test przetwarzania pliku przez orchestrator"""
    # Przygotowanie mocków
    mock_db = MagicMock()
    mock_profile_manager = MagicMock(spec=ProfileManager)
    mock_profile_manager.get_or_create_profile = AsyncMock(return_value={"id": "test_user"})
    mock_profile_manager.log_activity = AsyncMock()
    
    mock_intent_detector = MagicMock(spec=SimpleIntentDetector)
    mock_agent_router = MagicMock(spec=AgentRouter)
    mock_agent_router.route = AsyncMock(return_value=MagicMock())
    
    mock_memory_manager = MagicMock(spec=MemoryManager)
    mock_memory_manager.get_context = AsyncMock(return_value={})
    
    mock_response_generator = MagicMock(spec=ResponseGenerator)
    mock_response_generator.generate = AsyncMock(
        return_value=AgentResponse(
            success=True,
            text="Plik został przetworzony pomyślnie.",
            message="Plik został przetworzony pomyślnie."
        )
    )
    
    # Tworzenie orchestratora z mockami
    orchestrator = Orchestrator(
        db_session=mock_db,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator
    )
    
    # Wywołanie metody process_file
    file_bytes = b"test file content"
    filename = "test.jpg"
    session_id = "test_session"
    content_type = "image/jpeg"
    
    with patch.object(orchestrator, "_format_error_response") as mock_error:
        mock_error.return_value = AgentResponse(success=True, text="Plik przetworzony")
        
        result = await orchestrator.process_file(
            file_bytes=file_bytes,
            filename=filename,
            session_id=session_id,
            content_type=content_type
        )
    
    # Weryfikacja
    assert result.success is True
    
    # Sprawdzenie czy odpowiednie metody zostały wywołane
    mock_profile_manager.get_or_create_profile.assert_called_once_with(session_id)
    mock_profile_manager.log_activity.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_process_command():
    """Test przetwarzania komendy przez orchestrator"""
    # Przygotowanie mocków
    mock_db = MagicMock()
    mock_profile_manager = MagicMock(spec=ProfileManager)
    mock_profile_manager.get_or_create_profile = AsyncMock(return_value={"id": "test_user"})
    mock_profile_manager.log_activity = AsyncMock()
    
    mock_intent_detector = MagicMock(spec=SimpleIntentDetector)
    mock_intent_detector.detect_intent = AsyncMock(return_value="shopping")
    
    mock_agent_router = MagicMock(spec=AgentRouter)
    mock_agent = MagicMock()
    mock_agent.process = AsyncMock(
        return_value=AgentResponse(
            success=True,
            text="Dodano produkty do listy zakupów.",
            message="Dodano produkty do listy zakupów."
        )
    )
    mock_agent_router.route.return_value = mock_agent
    
    mock_memory_manager = MagicMock(spec=MemoryManager)
    mock_memory_manager.get_context = AsyncMock(return_value={})
    mock_memory_manager.update_context = AsyncMock()
    
    mock_response_generator = MagicMock(spec=ResponseGenerator)
    mock_response_generator.generate = AsyncMock(
        return_value=AgentResponse(
            success=True,
            text="Dodano produkty do listy zakupów.",
            message="Dodano produkty do listy zakupów."
        )
    )
    
    # Tworzenie orchestratora z mockami
    orchestrator = Orchestrator(
        db_session=mock_db,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
        agent_router=mock_agent_router,
        memory_manager=mock_memory_manager,
        response_generator=mock_response_generator
    )
    
    # Wywołanie metody process_command
    command = "Dodaj mleko do listy zakupów"
    session_id = "test_session"
    
    # Patch metody circuit_breaker.call_async
    with patch.object(orchestrator.circuit_breaker, "call_async") as mock_circuit_breaker:
        mock_circuit_breaker.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
        
        result = await orchestrator.process_command(
            user_command=command,
            session_id=session_id
        )
    
    # Weryfikacja
    assert result.success is True
    assert "Dodano produkty" in result.text
    
    # Sprawdzenie czy odpowiednie metody zostały wywołane
    mock_profile_manager.get_or_create_profile.assert_called_once_with(session_id)
    mock_memory_manager.get_context.assert_called_once()
    mock_intent_detector.detect_intent.assert_called_once()
    mock_agent_router.route.assert_called_once()
    mock_agent.process.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-v", "test_orchestrator.py"]) 