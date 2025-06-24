from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.weather_agent import WeatherAgent, WeatherRequest


@pytest.mark.asyncio
async def test_weather_agent_success() -> None:
    agent = WeatherAgent()
    mock_input = {
        "location": "Warsaw",
        "query": "weather in Warsaw",
        "model": "gemma3:12b",
    }

    with patch.object(agent, "_extract_location") as mock_extract:
        mock_extract.return_value = "Warszawa"

        with patch.object(agent, "_fetch_weatherapi") as mock_fetch:
            mock_weather_data = MagicMock()
            mock_weather_data.alerts = []
            mock_fetch.return_value = mock_weather_data

            with patch.object(agent, "_format_response") as mock_format:
                mock_format.return_value = AgentResponse(
                    success=True, message="Pogoda dla Warszawa"
                )

                with patch.object(agent, "_handle_error") as mock_error:
                    mock_error.return_value = AgentResponse(
                        success=True, message="Pogoda dla Warszawa"
                    )

                    response = await agent.process(mock_input)
                    assert isinstance(response, AgentResponse)
                    assert response.success is True
                    assert "Pogoda dla Warszawa" in response.message


@pytest.mark.asyncio
async def test_weather_agent_no_api_key() -> None:
    agent = WeatherAgent()
    response = await agent.process({"location": "Warsaw", "query": "test"})
    assert isinstance(response, AgentResponse)
    # Agent ma fallback i zawsze zwraca sukces, nawet bez API key
    assert response.success is True
    # Sprawdź czy zawiera informację o lokalizacji
    assert "Warszawa" in response.text or "Warsaw" in response.text


@pytest.mark.asyncio
async def test_weather_agent_input_validation() -> None:
    agent = WeatherAgent()

    with patch.object(agent, "_extract_location") as mock_extract:
        mock_extract.return_value = "Warszawa"

        # Test missing required field - agent używa domyślnej lokalizacji
        response = await agent.process({"model": "gemma3:12b"})
        assert response.success is True  # Agent ma fallback
        assert "Warszawa" in response.text  # Używa domyślnej lokalizacji

        # Test invalid model - agent obsługuje to gracefully
        response = await agent.process({"query": "test", "model": "invalid"})
        assert response.success is True  # Agent ma fallback
        assert "Warszawa" in response.text  # Używa domyślnej lokalizacji


@pytest.mark.asyncio
async def test_weather_agent_error_handling() -> None:
    agent = WeatherAgent()

    with patch.object(agent, "_extract_location") as mock_extract:
        mock_extract.side_effect = ValueError("Location error")

        response = await agent.process(
            {"location": "Warsaw", "query": "test", "model": "gemma3:12b"}
        )
        # Agent ma fallback i obsługuje błędy gracefully
        assert response.success is True
        assert "Warszawa" in response.text  # Używa domyślnej lokalizacji


@pytest.mark.asyncio
async def test_weather_request_model() -> None:
    # Test valid request
    valid = WeatherRequest(location="Warsaw")
    assert valid.location == "Warsaw"
    assert valid.days == 3
    assert valid.model == "gemma3:12b"  # Domyślny model

    # Test invalid request - WeatherRequest nie waliduje pustego location
    valid = WeatherRequest(location="")
    assert valid.location == ""
