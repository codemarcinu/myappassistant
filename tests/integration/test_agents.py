import os
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.chef_agent import ChefAgent
from backend.agents.meal_planner_agent import MealPlannerAgent
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent
from backend.core.hybrid_llm_client import hybrid_llm_client


# --- Wzorzec do mockowania LLM w testach agentów ---
def make_llm_chat_mock(stream_content: str, non_stream_content: str = None):
    """
    Zwraca funkcję do mockowania llm_client.chat/hybrid_llm_client.chat,
    która obsługuje zarówno stream=True (async generator), jak i stream=False (dict).
    """

    async def stream_chat(*args, **kwargs):
        yield {"message": {"content": stream_content}}

    async def non_stream_chat(*args, **kwargs):
        return {"message": {"content": non_stream_content or stream_content}}

    def chat_mock(*args, **kwargs):
        if kwargs.get("stream"):
            return stream_chat(*args, **kwargs)
        else:
            return non_stream_chat(*args, **kwargs)

    class HybridLLMMock:
        chat = staticmethod(chat_mock)

    return chat_mock, HybridLLMMock


# --- Testy agentów ---


@pytest.mark.asyncio
@patch("backend.agents.weather_agent.llm_client", new_callable=AsyncMock)
async def test_weather_agent(mock_llm_client):
    """Tests the WeatherAgent's logic."""

    # Mock API keys
    os.environ["WEATHER_API_KEY"] = "dummy"
    os.environ["OPENWEATHER_API_KEY"] = "dummy"

    # Arrange
    chat_mock, HybridLLMMock = make_llm_chat_mock("Słonecznie, 25 stopni.")
    mock_llm_client.chat = chat_mock

    # Patch hybrid_llm_client.chat directly
    with patch.object(hybrid_llm_client, "chat", new=chat_mock):
        # Mock httpx.AsyncClient instance
        with patch("httpx.AsyncClient") as mock_http_client_class:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={"current": {"temp_c": 25}})
            mock_response.raise_for_status = AsyncMock()

            mock_async_client_instance = AsyncMock()
            mock_async_client_instance.get.return_value = mock_response
            mock_http_client_class.return_value = mock_async_client_instance

            agent = WeatherAgent()

            # Act - przekazuję location zgodnie z modelem WeatherRequest
            result = await agent.process(
                {"location": "Warszawa", "model": "test-model"}
            )

            # Assert
            assert result.success
            response_text = ""
            async for chunk in result.text_stream:
                response_text += chunk
            assert "Słonecznie, 25 stopni." in response_text


@pytest.mark.asyncio
@patch("backend.agents.search_agent.llm_client", new_callable=AsyncMock)
@patch("backend.agents.search_agent.httpx.AsyncClient")
async def test_search_agent(mock_http_client, mock_llm_client):
    """Tests the SearchAgent's logic."""
    chat_mock, _ = make_llm_chat_mock("Wyniki dla 'Python'.")
    mock_llm_client.chat = chat_mock

    # Mock response data properly
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={
            "RelatedTopics": [
                {"Text": "Python language", "FirstURL": "http://example.com"}
            ]
        }
    )
    mock_response.raise_for_status = AsyncMock()
    mock_async_client = AsyncMock()
    mock_async_client.get.return_value = mock_response
    mock_http_client.return_value.__aenter__.return_value = mock_async_client

    agent = SearchAgent()
    # Act
    result = await agent.process({"query": "Python", "model": "test-model"})
    # Assert
    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert "Wyniki dla 'Python'." in response_text


@pytest.mark.asyncio
@patch("backend.agents.chef_agent.llm_client", new_callable=AsyncMock)
@patch(
    "backend.agents.chef_agent.get_available_products_from_pantry",
    new_callable=AsyncMock,
)
async def test_chef_agent(mock_get_products, mock_llm_client):
    """Tests the ChefAgent's logic."""
    mock_get_products.return_value = [AsyncMock(name="Mleko", id=1)]
    chat_mock, HybridLLMMock = make_llm_chat_mock(
        "PRZEPIS: Zrób owsiankę. UŻYTE SKŁADNIKI: Mleko", "Mleko"
    )
    mock_llm_client.chat = chat_mock
    mock_llm_client.generate_stream = chat_mock

    # Patch hybrid_llm_client.chat directly
    with patch.object(hybrid_llm_client, "chat", new=chat_mock):
        agent = ChefAgent()
        mock_db = AsyncMock()
        result = await agent.process(
            {
                "db": mock_db,
                "model": "test-model",
                "ingredients": ["Mleko", "Płatki owsiane"],
            }
        )
        assert result.success
        response_text = ""
        async for chunk in result.text_stream:
            response_text += chunk
        assert "Zrób owsiankę" in response_text


@pytest.mark.asyncio
@patch("backend.agents.meal_planner_agent.llm_client", new_callable=AsyncMock)
@patch(
    "backend.agents.meal_planner_agent.get_available_products", new_callable=AsyncMock
)
async def test_meal_planner_agent(mock_get_products, mock_llm_client):
    """Tests the MealPlannerAgent's logic."""
    product_mock = AsyncMock()
    product_mock.name = "Jajka"
    mock_get_products.return_value = [product_mock]

    async def stream_generator(*args, **kwargs):
        yield {
            "message": {
                "content": '{"meal_plan": [{"day": "Monday", "breakfast": "Jajecznica"}]}'
            }
        }

    mock_llm_client.generate_stream = stream_generator
    agent = MealPlannerAgent(name="TestMealPlanner")
    mock_db = AsyncMock()
    result = await agent.process({"db": mock_db})
    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert "Jajecznica" in response_text
