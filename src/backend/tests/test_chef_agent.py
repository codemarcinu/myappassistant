from unittest.mock import AsyncMock, patch

import pytest
from unittest.mock import MagicMock

from backend.agents.interfaces import AgentResponse
from backend.agents.chef_agent import ChefAgent


@pytest.mark.asyncio
async def test_chef_agent_streaming():
    agent = ChefAgent()
    mock_context = {
        "available_ingredients": ["chicken", "rice"],
        "dietary_restrictions": None,
    }

    # Mock the streaming response
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = [
        {"message": {"content": "Recipe part 1"}},
        {"message": {"content": "Recipe part 2"}},
    ]

    with patch("backend.core.llm_client.llm_client.chat", return_value=mock_stream):
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
    response = await agent.process({"available_ingredients": []})
    assert response.success is False
    assert "validation error" in response.error.lower()
    assert "available_ingredients" in response.error


@pytest.mark.asyncio
async def test_chef_agent_input_validation():
    agent = ChefAgent()

    # Test valid input
    valid_input = {
        "available_ingredients": ["chicken", "rice"],
        "dietary_restrictions": "vegetarian",
    }
    response = await agent.process(valid_input)
    assert response.success is True


@pytest.mark.asyncio
async def test_chef_agent_dietary_restrictions():
    agent = ChefAgent()
    mock_context = {
        "available_ingredients": ["tofu", "rice"],
        "dietary_restrictions": "vegetarian",
    }

    # Mock streaming response
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = [
        {"message": {"content": "Vegetarian recipe part 1"}},
        {"message": {"content": "Vegetarian recipe part 2"}},
    ]

    with patch("backend.core.llm_client.llm_client.chat", return_value=mock_stream):
        response = await agent.process(mock_context)
        assert response.success is True

        content = ""
        async for chunk in response.text_stream:
            content += chunk
        assert "Vegetarian recipe part 1Vegetarian recipe part 2" in content


@pytest.mark.asyncio
async def test_chef_agent_llm_error():
    agent = ChefAgent()
    mock_context = {
        "available_ingredients": ["chicken", "rice"],
        "dietary_restrictions": None,
    }

    with patch("backend.agents.chef_agent.llm_client.chat") as mock_chat:
        mock_chat.side_effect = Exception("LLM Error")

        response = await agent.process(mock_context)
        assert (
            response.success is True
        )  # Agent zwraca success=True nawet przy błędzie LLM
        assert response.text_stream is not None  # Ale zwraca stream z błędem
