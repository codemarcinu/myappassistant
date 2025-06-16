from unittest.mock import patch

import pytest

from backend.agents.base_agent import AgentResponse
from backend.agents.chef_agent import ChefAgent


@pytest.mark.asyncio
async def test_chef_agent_streaming():
    agent = ChefAgent()
    mock_context = {"ingredients": ["chicken", "rice"], "dietary_restrictions": None}

    with patch("backend.core.llm_client.llm_client.generate_stream") as mock_stream:
        mock_stream.return_value = [
            {"message": {"content": "Recipe part 1"}},
            {"message": {"content": "Recipe part 2"}},
        ]

        response = await agent.process(mock_context)
        assert isinstance(response, AgentResponse)
        assert response.success is True

        # Test streaming content
        content = ""
        async for chunk in response.text_stream:
            content += chunk
        assert "Recipe part 1Recipe part 2" in content


@pytest.mark.asyncio
async def test_chef_agent_error_handling():
    agent = ChefAgent()
    mock_context = {"ingredients": [], "dietary_restrictions": None}

    response = await agent.process(mock_context)
    assert response.success is False
    assert "No ingredients provided" in response.error
