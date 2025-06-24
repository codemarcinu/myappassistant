from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.meal_planner_agent import MealPlannerAgent


@pytest.mark.asyncio
async def test_meal_planner_with_products() -> None:
    agent = MealPlannerAgent()
    mock_input = {"dietary_restrictions": "vegetarian", "db": AsyncMock()}

    with patch(
        "backend.agents.meal_planner_agent.get_available_products"
    ) as mock_get_products:
        mock_get_products.return_value = [
            {"name": "Tomato", "category": "vegetables"},
            {"name": "Rice", "category": "grains"},
        ]

        with patch("backend.core.llm_client.llm_client.chat") as mock_chat:
            mock_chat.return_value = {
                "message": {"content": "Plan posiłków dla wegetarianina"}
            }

            response = await agent.process(mock_input)
            assert hasattr(response, "success")
            assert response.success is True


@pytest.mark.asyncio
async def test_meal_planner_no_products() -> None:
    agent = MealPlannerAgent()
    mock_input = {"dietary_restrictions": "vegetarian", "db": AsyncMock()}

    with patch(
        "backend.agents.meal_planner_agent.get_available_products"
    ) as mock_get_products:
        mock_get_products.return_value = []

        response = await agent.process(mock_input)
        assert hasattr(response, "success")
        assert response.success is True  # Agent zwraca success=True nawet bez produktów
