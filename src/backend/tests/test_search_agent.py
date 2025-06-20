from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.base_agent import AgentResponse
from backend.agents.search_agent import SearchAgent


@pytest.mark.asyncio
async def test_search_agent_with_results():
    agent = SearchAgent()
    mock_context = {"query": "test query", "model": "llama3"}

    with patch(
        "backend.agents.search_agent.SearchAgent._perform_search"
    ) as mock_search:
        mock_search.return_value = {
            "success": True,
            "content": "Test search results",
            "data": [
                {
                    "title": "Test Result",
                    "url": "http://test.com",
                    "snippet": "Test snippet",
                }
            ],
        }

        response = await agent.process(mock_context)
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert "Test search results" in response.text


@pytest.mark.asyncio
async def test_search_agent_empty_results():
    agent = SearchAgent()
    mock_context = {"query": "test query"}

    with patch(
        "backend.agents.search_agent.SearchAgent._perform_search"
    ) as mock_search:
        mock_search.return_value = {
            "success": True,
            "content": "Nie znaleziono odpowiednich wyników.",
            "data": [],
        }

        response = await agent.process(mock_context)
        assert response.success is True  # Empty results are handled gracefully
        assert "Nie znaleziono" in response.text


@pytest.mark.asyncio
async def test_search_agent_input_validation():
    agent = SearchAgent()

    # Test empty query
    mock_context = {"query": ""}
    response = await agent.process(mock_context)
    assert response.success is False
    assert "Query is required" in response.error  # Rzeczywisty komunikat błędu

    # Test missing query
    mock_context = {}
    response = await agent.process(mock_context)
    assert response.success is False
    assert "Query is required" in response.error


@pytest.mark.asyncio
async def test_search_agent_llm_error():
    agent = SearchAgent()
    mock_input = {"query": "test query"}

    with patch("backend.integrations.web_search.web_search") as mock_search:
        mock_search.return_value = [{"title": "Test", "url": "http://test.com"}]

        with patch(
            "backend.core.hybrid_llm_client.hybrid_llm_client.chat"
        ) as mock_chat:
            mock_chat.side_effect = Exception("LLM Error")

            response = await agent.process(mock_input)
            # Agent ma fallback do DuckDuckGo i zwraca sukces
            assert response.success is True
            assert "Nie znaleziono" in response.text or "Odpowiedź" in response.text
