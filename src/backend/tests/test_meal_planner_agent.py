from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.base_agent import AgentResponse
from backend.agents.meal_planner_agent import MealPlannerAgent


@pytest.mark.asyncio
async def test_meal_planner_with_products():
    agent = MealPlannerAgent()
    mock_db = AsyncMock()
    mock_db.execute.return_value = [
        {"name": "chicken", "quantity": 2},
        {"name": "rice", "quantity": 1},
    ]
    mock_context = {"db": mock_db}

    with patch("backend.core.llm_client.llm_client.generate_stream") as mock_stream:
        mock_stream.return_value = [
            {"message": {"content": "Meal plan part 1"}},
            {"message": {"content": "Meal plan part 2"}},
        ]

        response = await agent.process(mock_context)
        assert isinstance(response, AgentResponse)
        assert response.success is True

        content = ""
        async for chunk in response.text_stream:
            content += chunk
        assert "Meal plan part 1Meal plan part 2" in content


@pytest.mark.asyncio
async def test_meal_planner_no_products():
    agent = MealPlannerAgent()
    mock_db = AsyncMock()
    mock_db.execute.return_value = []
    mock_context = {"db": mock_db}

    response = await agent.process(mock_context)
    assert response.success is False
    assert "No products available" in response.error
