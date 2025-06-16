from unittest.mock import patch

import pytest

from backend.agents.base_agent import AgentResponse
from backend.agents.search_agent import SearchAgent


@pytest.mark.asyncio
async def test_search_agent_with_results():
    agent = SearchAgent()
    mock_context = {"query": "test query"}

    with patch("backend.agents.search_agent.search") as mock_search:
        mock_search.return_value = [{"title": "Test Result", "link": "http://test.com"}]

        with patch("backend.core.llm_client.llm_client.generate_stream") as mock_stream:
            mock_stream.return_value = [
                {"message": {"content": "Search result 1"}},
                {"message": {"content": "Search result 2"}},
            ]

            response = await agent.process(mock_context)
            assert isinstance(response, AgentResponse)
            assert response.success is True

            content = ""
            async for chunk in response.text_stream:
                content += chunk
            assert "Search result 1Search result 2" in content


@pytest.mark.asyncio
async def test_search_agent_empty_results():
    agent = SearchAgent()
    mock_context = {"query": "test query"}

    with patch("backend.agents.search_agent.search") as mock_search:
        mock_search.return_value = []

        response = await agent.process(mock_context)
        assert response.success is False
        assert "No results found" in response.error
