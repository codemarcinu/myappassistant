import os

import pytest
import pytest_asyncio

from backend.agents.chef_agent import ChefAgent
from backend.agents.meal_planner_agent import MealPlannerAgent
from backend.agents.search_agent import SearchAgent
from backend.agents.weather_agent import WeatherAgent
from backend.core.database import AsyncSessionLocal
from backend.core.hybrid_llm_client import hybrid_llm_client
from backend.infrastructure.vector_store.vector_store_impl import (
    EnhancedVectorStoreImpl,
)


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_live_weather_agent():
    """Tests the WeatherAgent against the live Ollama service."""
    # Sprawdź czy klucz API jest dostępny
    if not os.getenv("OPENWEATHER_API_KEY"):
        pytest.skip("Weather API key not available")

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
    # Sprawdź czy klucz API jest dostępny
    use_perplexity = (
        os.getenv("PERPLEXITY_API_KEY")
        and os.getenv("PERPLEXITY_API_KEY") != "your_perplexity_api_key_here"
    )

    vector_store = EnhancedVectorStoreImpl(llm_client=hybrid_llm_client)
    agent = SearchAgent(vector_store=vector_store, llm_client=hybrid_llm_client)

    # Użyj DuckDuckGo jako fallback jeśli Perplexity nie jest dostępny
    result = await agent.process(
        {
            "query": "co to jest Python?",
            "model": "gemma3:12b",
            "use_perplexity": use_perplexity,
        }
    )

    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert len(response_text) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_live_chef_agent(db_session):
    """Tests the ChefAgent against the live Ollama service."""
    agent = ChefAgent()
    result = await agent.process(
        {
            "db": db_session,
            "model": "gemma3:12b",
            "available_ingredients": ["pomidory", "ser", "makaron"],
        }
    )

    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert len(response_text) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_live_meal_planner_agent(db_session):
    """Tests the MealPlannerAgent against the live Ollama service."""
    agent = MealPlannerAgent(name="LiveMealPlanner")
    result = await agent.process({"db": db_session})

    assert result.success
    response_text = ""
    async for chunk in result.text_stream:
        response_text += chunk
    assert "plan" in response_text.lower()
