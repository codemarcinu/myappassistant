import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
from pydantic import BaseModel

from backend.agents.base_agent import AgentResponse, EnhancedBaseAgent
from backend.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class WeatherRequest(BaseModel):
    """Model for weather request parameters"""

    location: str
    days: Optional[int] = 1
    model: Optional[str] = "gemma3:12b"


class WeatherAgent(EnhancedBaseAgent[WeatherRequest]):
    """Agent that fetches weather forecasts"""

    def __init__(self, name: str = "WeatherAgent", api_key: Optional[str] = None):
        super().__init__(name)
        self.input_model = WeatherRequest
        self.api_key = api_key or os.getenv("WEATHER_API_KEY") or "demo_key"
        if self.api_key == "demo_key":
            logger.warning("Weather API key not configured - using demo mode")
        self.base_url = "https://api.weatherapi.com/v1"

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process a weather forecast request"""
        try:
            validated_data = self._validate_input(input_data)
            query = validated_data.get("query", "")
            model = validated_data.get("model", "gemma3:12b")

            # Use LLM to extract location
            location = await self._extract_location(query, model)
            if not location:
                return self._handle_error(
                    ValueError("Nie mogłem rozpoznać lokalizacji w zapytaniu.")
                )
                # Remove duplicate location check

            # Fetch weather data
            weather_data = await self._fetch_weather(location)
            if not weather_data:
                return self._handle_error(
                    ValueError(f"Nie udało się pobrać prognozy pogody dla {location}")
                )

            # Format response with LLM
            response_stream = self._format_weather_response(
                location, weather_data, model
            )

            # Get detailed weather data
            api_url = f"{self.base_url}/forecast.json"
            params = {"key": self.api_key, "q": location, "days": 3, "lang": "pl"}

            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                weather_json = response.json()

                return AgentResponse(
                    success=True,
                    data={
                        "location": location,
                        "current": weather_json.get("current", {}),
                        "forecast": weather_json.get("forecast", {}).get(
                            "forecastday", []
                        ),
                    },
                    text_stream=response_stream,
                    message=f"Pogoda dla {location}",
                )

        except httpx.HTTPStatusError as e:
            return self._handle_error(e)
        except Exception as e:
            return self._handle_error(e)

    async def _extract_location(self, query: str, model: str) -> str:
        """Extract location from user query using LLM"""
        prompt = (
            f"Przeanalizuj poniższe zapytanie i wyodrębnij nazwę lokalizacji (miasto, kraj itp.):\n\n"
            f"Zapytanie: '{query}'\n\n"
            f"Zwróć tylko nazwę lokalizacji, bez dodatkowego tekstu. Jeśli nie ma lokalizacji, zwróć 'Warszawa'."
        )

        try:
            # Log the extraction attempt
            logging.info(
                f"Extracting location from query: '{query}' using model: {model}"
            )

            # Use try/except to catch any LLM errors
            try:
                await llm_client.chat(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Jesteś pomocnym asystentem, który ekstrahuje lokalizacje z tekstu.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    stream=False,
                )

                response = await llm_client.chat(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Jesteś pomocnym asystentem, który ekstrahuje lokalizacje z tekstu.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    stream=False,
                )

                logging.info(f"LLM response for location extraction: {response}")

                # Check if response has expected structure
                if not response or not response.get("message"):
                    logging.warning(
                        "Invalid LLM response format for location extraction, defaulting to Warsaw"
                    )
                    return "Warszawa"  # Default to Warsaw if extraction fails

                location = response["message"]["content"].strip()
                logging.info(f"Extracted location: '{location}'")
                return location
            except Exception as e:
                logging.error(f"Error in LLM location extraction: {str(e)}")
                return "Warszawa"  # Default to Warsaw in case of any error
        except Exception as e:
            logger.error(f"Error extracting location: {e}")
            return "Warszawa"  # Default to Warsaw

    async def _fetch_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather data from the API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast.json",
                    params={
                        "key": self.api_key,
                        "q": location,
                        "days": 3,
                        "aqi": "no",
                        "alerts": "no",
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather data for {location}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching weather data for {location}: {e}")
            return {}

    async def _format_weather_response(
        self, location: str, weather_data: Dict[str, Any], model: str
    ) -> AsyncGenerator[str, None]:
        """Format weather data into a user-friendly response using LLM stream"""
        current = weather_data.get("current", {})
        forecast = weather_data.get("forecast", {}).get("forecastday", [])

        weather_summary = (
            f"Lokalizacja: {location}\n"
            f"Aktualna temperatura: {current.get('temp_c', 'N/A')}°C\n"
            f"Warunki: {current.get('condition', {}).get('text', 'N/A')}\n"
            f"Wiatr: {current.get('wind_kph', 'N/A')} km/h\n"
            f"Wilgotność: {current.get('humidity', 'N/A')}%\n\n"
        )

        if forecast:
            weather_summary += "Prognoza na najbliższe dni:\n"
            for day in forecast:
                weather_summary += (
                    f"- {day.get('date', 'N/A')}: "
                    f"{day.get('day', {}).get('mintemp_c', 'N/A')}°C to "
                    f"{day.get('day', {}).get('maxtemp_c', 'N/A')}°C, "
                    f"{day.get('day', {}).get('condition', {}).get('text', 'N/A')}\n"
                )

        prompt = (
            f"Na podstawie poniższych danych pogodowych, utwórz przyjazną i naturalnie brzmiącą "
            f"prognozę pogody w języku polskim:\n\n{weather_summary}"
        )

        messages = [
            {"role": "system", "content": "Jesteś pomocnym asystentem pogodowym."},
            {"role": "user", "content": prompt},
        ]

        async for chunk in self._stream_llm_response(model, messages):
            yield chunk
