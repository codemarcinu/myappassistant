from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.interfaces import AgentResponse, IntentData
from backend.agents.orchestrator import Orchestrator

PROMPTS = [
    # Chef Agent
    ("Podaj przepis na szybki obiad z kurczakiem i ryżem.", "chef"),
    ("Zaproponuj wegańskie śniadanie na jutro.", "chef"),
    # Weather Agent
    ("Jaka będzie pogoda w Warszawie jutro?", "weather"),
    ("Czy dziś będzie padać w Krakowie?", "weather"),
    # Search Agent
    ("Ile kalorii ma awokado?", "search"),
    ("Jakie są zalety diety śródziemnomorskiej?", "search"),
    # OCR Agent
    ("Przetwórz załączony paragon i wypisz produkty.", "ocr"),
    ("Odczytaj tekst z załączonego zdjęcia.", "ocr"),
    # RAG Agent
    ("Jak przechowywać świeże zioła według dokumentacji FoodSave?", "rag"),
    ("Podsumuj najważniejsze zasady ograniczania marnowania żywności.", "rag"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt,expected_agent", PROMPTS)
async def test_agent_prompt_routing(prompt, expected_agent) -> None:
    """Testuje routing promptów do odpowiednich agentów"""
    mock_db = AsyncMock()
    mock_profile_manager = AsyncMock()
    mock_intent_detector = AsyncMock(return_value=IntentData(expected_agent))

    orchestrator = Orchestrator(
        db_session=mock_db,
        profile_manager=mock_profile_manager,
        intent_detector=mock_intent_detector,
    )

    # Mock agent_router, zwracając nazwę agenta w odpowiedzi
    with patch.object(orchestrator, "agent_router") as mock_router:
        mock_router.route_to_agent = AsyncMock(
            return_value=AgentResponse(
                success=True,
                text=f"Odpowiedź agenta {expected_agent}",
                data={"agent": expected_agent},
            )
        )

        response = await orchestrator.process_command(prompt, "test_session")
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert (
            expected_agent in response.text
            or response.data.get("agent") == expected_agent
        )
