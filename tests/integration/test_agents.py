from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.chef_agent import ChefAgent
from backend.agents.meal_planner_agent import MealPlannerAgent
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent


@pytest.mark.asyncio
@patch("backend.agents.weather_agent.llm_client", new_callable=AsyncMock)
@patch("backend.agents.weather_agent.httpx.AsyncClient")
async def test_weather_agent(mock_http_client, mock_llm_client):
    """Tests the WeatherAgent's logic."""

    # Arrange
    async def stream_generator(content):
        yield {"message": {"content": content}}

    mock_llm_client.chat.side_effect = [
        {"message": {"content": "Warszawa"}},  # Location extraction is not streamed
        stream_generator("Słonecznie, 25 stopni."),  # Formatting is streamed
    ]

    mock_response = MagicMock()
    mock_response.json.return_value = {"current": {"temp_c": 25}}

    mock_async_client = AsyncMock()
    mock_async_client.get.return_value = mock_response
    mock_http_client.return_value.__aenter__.return_value = mock_async_client

    agent = WeatherAgent()

    # Act
    result = await agent.process({"query": "pogoda w warszawie", "model": "test-model"})

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

    # Arrange
    async def stream_generator(content):
        yield {"message": {"content": content}}

    mock_llm_client.chat.return_value = stream_generator("Wyniki dla 'Python'.")

    mock_response = AsyncMock()
    mock_response.json.return_value = {"RelatedTopics": [{"Text": "Python language"}]}

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

    # Arrange
    async def stream_generator(content):
        yield {"message": {"content": content}}

    mock_get_products.return_value = [MagicMock(name="Mleko", id=1)]
    mock_llm_client.chat.return_value = stream_generator(
        "PRZEPIS: Zrób owsiankę. UŻYTE SKŁADNIKI: Mleko"
    )

    agent = ChefAgent()
    mock_db = AsyncMock()

    # Act
    result = await agent.process({"db": mock_db, "model": "test-model"})

    # Assert
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
    # Arrange
    product_mock = MagicMock()
    product_mock.name = "Jajka"
    mock_get_products.return_value = [product_mock]

    async def stream_generator(content):
        yield {"message": {"content": content}}

    mock_llm_client.chat.return_value = stream_generator(
        '{"meal_plan": [{"day": "Monday", "breakfast": "Jajecznica"}]}'
    )

    agent = MealPlannerAgent(name="TestMealPlanner")
    mock_db = AsyncMock()

    # Act
    result = await agent.process({"db": mock_db})

    # Assert
    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert "Jajecznica" in response_text
