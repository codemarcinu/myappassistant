from unittest.mock import patch

import pytest

from backend.agents.base_agent import AgentResponse
from backend.agents.weather_agent import WeatherAgent


@pytest.mark.asyncio
async def test_weather_agent_success():
    agent = WeatherAgent(api_key="test_key")
    mock_input = {"query": "weather in Warsaw", "model": "gemma3:12b"}

    with patch(
        "backend.agents.weather_agent.WeatherAgent._extract_location"
    ) as mock_extract:
        mock_extract.return_value = "Warszawa"

        with patch("backend.agents.weather_agent.httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "current": {"temp_c": 20, "condition": {"text": "Sunny"}},
                "forecast": {"forecastday": []},
            }

            with patch(
                "backend.core.llm_client.llm_client.generate_stream"
            ) as mock_stream:
                mock_stream.return_value = [
                    {"message": {"content": "Pogoda w Warszawie"}},
                    {"message": {"content": "20°C, Sunny"}},
                ]

                response = await agent.process(mock_input)
                assert isinstance(response, AgentResponse)
                assert response.success is True
                assert "Pogoda dla Warszawa" in response.message

                content = ""
                async for chunk in response.text_stream:
                    content += chunk
                assert "Pogoda w Warszawie" in content


@pytest.mark.asyncio
async def test_weather_agent_no_api_key():
    agent = WeatherAgent(api_key=None)
    response = await agent.process({"query": "test"})
    assert isinstance(response, AgentResponse)
    assert response.success is False
    assert "Nie udało się pobrać prognozy pogody" in response.error
