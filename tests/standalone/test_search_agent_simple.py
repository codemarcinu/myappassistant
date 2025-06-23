from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_perplexity_client():
    mock = AsyncMock()
    mock.search = AsyncMock(
        return_value={
            "success": True,
            "content": "Mocked search results",
            "query": "test query",
            "model": "llama-3.1-8b-instruct",
        }
    )
    return mock


@pytest.fixture
def mock_llm_client():
    return AsyncMock()


@pytest.fixture
def mock_vector_store():
    return AsyncMock()


@pytest.fixture
def search_agent(mock_vector_store, mock_llm_client, mock_perplexity_client):
    # Import SearchAgent bezpośrednio
    from backend.agents.search_agent import SearchAgent

    return SearchAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
        perplexity_client=mock_perplexity_client,
    )


async def collect_stream_text(response):
    collected = ""
    async for chunk in response.text_stream:
        collected += chunk
    return collected


@pytest.mark.asyncio
async def test_web_search_success(search_agent, mock_perplexity_client):
    """Test podstawowego wyszukiwania"""
    response = await search_agent.process({"query": "test"})
    collected_text = await collect_stream_text(response)

    assert response.success is True
    assert "search results" in collected_text.lower()
    mock_perplexity_client.search.assert_called_once()


@pytest.mark.asyncio
async def test_web_search_empty_query(search_agent):
    """Test wyszukiwania z pustym zapytaniem"""
    response = await search_agent.process({"query": ""})

    assert response.success is False
    assert "Query is required" in response.error


@pytest.mark.asyncio
async def test_web_search_with_max_results(search_agent, mock_perplexity_client):
    """Test wyszukiwania z określoną liczbą wyników"""
    response = await search_agent.process({"query": "test", "max_results": 10})
    collected_text = await collect_stream_text(response)

    assert response.success is True
    assert "search results" in collected_text.lower()
    # Sprawdź czy search został wywołany z max_results=10
    mock_perplexity_client.search.assert_called_once()
    call_args = mock_perplexity_client.search.call_args
    assert call_args[1]["max_results"] == 10
