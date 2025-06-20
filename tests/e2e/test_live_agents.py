import pytest

from backend.agents.chef_agent import ChefAgent
from backend.agents.meal_planner_agent import MealPlannerAgent
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent
from backend.core.database import AsyncSessionLocal


@pytest.mark.skip(reason="Weather API key not available")
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_live_weather_agent():
    """Tests the WeatherAgent against the live Ollama service."""
    agent = WeatherAgent()
    result = await agent.process(
        {"query": "jaka jest pogoda w Warszawie?", "model": "gemma3:12b"}
    )

    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert "Warszawa" in response_text
    assert "°C" in response_text


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_live_search_agent():
    """Tests the SearchAgent against the live Ollama service."""
    agent = SearchAgent()
    result = await agent.process({"query": "co to jest Python?", "model": "gemma3:12b"})

    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert "Python" in response_text


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_live_chef_agent():
    """Tests the ChefAgent against the live Ollama service."""
    agent = ChefAgent()
    async with AsyncSessionLocal() as db:
        result = await agent.process({"db": db, "model": "gemma3:12b"})

    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert len(response_text) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_live_meal_planner_agent():
    """Tests the MealPlannerAgent against the live Ollama service."""
    agent = MealPlannerAgent(name="LiveMealPlanner")
    async with AsyncSessionLocal() as db:
        result = await agent.process({"db": db})

    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert "plan" in response_text.lower()
