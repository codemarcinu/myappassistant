from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.search_agent import SearchAgent


@pytest.mark.asyncio
async def test_search_agent_with_results() -> None:
    mock_vector_store = AsyncMock()
    mock_llm_client = AsyncMock()
    agent = SearchAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)
    mock_context = {"query": "test query", "model": "llama3"}

    with patch(
        "backend.agents.search_agent.perplexity_client.search"
    ) as mock_web_search, patch(
        "backend.agents.search_agent.hybrid_llm_client.chat"
    ) as mock_chat:
        mock_web_search.return_value = {
            "success": True,
            "content": "LLM summary: Test search results",
        }
        mock_chat.return_value = {
            "message": {"content": "LLM summary: Test search results"}
        }

        response = await agent.process(mock_context)
        assert isinstance(response, AgentResponse)
        assert response.success is True

        # Consume the stream to get the text
        result_text = ""
        async for chunk in response.text_stream:
            result_text += chunk
        assert "LLM summary: Test search results" in result_text


@pytest.mark.asyncio
async def test_search_agent_empty_results() -> None:
    mock_vector_store = AsyncMock()
    mock_llm_client = AsyncMock()
    agent = SearchAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)
    mock_context = {"query": "test query"}

    with patch(
        "backend.agents.search_agent.perplexity_client.search"
    ) as mock_web_search:
        mock_web_search.return_value = {
            "success": True,
            "content": "Nie znaleziono odpowiednich wyników.",
        }

        response = await agent.process(mock_context)
        assert response.success is True  # Empty results are handled gracefully

        # Consume the stream
        result_text = ""
        async for chunk in response.text_stream:
            result_text += chunk
        assert "Nie znaleziono" in result_text


@pytest.mark.asyncio
async def test_search_agent_input_validation() -> None:
    mock_vector_store = AsyncMock()
    mock_llm_client = AsyncMock()
    agent = SearchAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)

    # Test empty query
    mock_context = {"query": ""}
    response = await agent.process(mock_context)
    assert response.success is False
    assert "Query is required" in response.error

    # Test missing query
    mock_context = {}
    response = await agent.process(mock_context)
    assert response.success is False
    assert "Query is required" in response.error


@pytest.mark.asyncio
async def test_search_agent_llm_error() -> None:
    mock_vector_store = AsyncMock()
    mock_llm_client = AsyncMock()
    agent = SearchAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)
    mock_input = {"query": "test query"}

    with patch("backend.agents.search_agent.perplexity_client.search") as mock_search:
        mock_search.return_value = {
            "success": False,
            "error": "LLM Error",
            "content": "Błąd podczas generowania odpowiedzi",
        }

        with patch("backend.agents.search_agent.hybrid_llm_client.chat") as mock_chat:
            mock_chat.side_effect = Exception("LLM Error")

            response = await agent.process(mock_input)
            assert response.success is True

            # Consume the stream
            result_text = ""
            if response.text_stream:
                async for chunk in response.text_stream:
                    result_text += chunk
            assert "Błąd podczas generowania odpowiedzi" in result_text
