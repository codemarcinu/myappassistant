import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class WeatherRequest(BaseModel):
    """Model for weather request parameters"""

    location: str
    days: Optional[int] = 1


class WeatherAgent(BaseAgent):
    """Agent that fetches weather forecasts"""

    def __init__(self, name: str = "WeatherAgent"):
        super().__init__(name)
        self.api_key = "demo_key"  # Would normally be loaded from environment variables
        self.base_url = "https://api.weatherapi.com/v1"

    async def process(self, input_data: Any) -> AgentResponse:
        """Process a weather forecast request"""
        if isinstance(input_data, dict):
            try:
                # Extract location from input
                query = input_data.get("query", "")

                # Use LLM to extract location
                location = await self._extract_location(query)
                if not location:
                    return AgentResponse(
                        success=False,
                        error="Nie mogłem rozpoznać lokalizacji w zapytaniu.",
                        text="Nie mogłem rozpoznać lokalizacji w zapytaniu.",
                    )

                # Fetch weather data
                weather_data = await self._fetch_weather(location)
                if not weather_data:
                    return AgentResponse(
                        success=False,
                        error=f"Nie udało się pobrać prognozy pogody dla {location}.",
                        text=f"Nie udało się pobrać prognozy pogody dla {location}.",
                    )

                # Format response with LLM
                response = await self._format_weather_response(location, weather_data)

                return AgentResponse(
                    success=True,
                    data=weather_data,
                    text=response,
                    message=f"Pogoda dla {location}",
                )
            except Exception as e:
                logger.error(f"Error processing weather request: {e}")
                return AgentResponse(
                    success=False,
                    error=f"Wystąpił błąd podczas przetwarzania zapytania: {str(e)}",
                    text="Przepraszam, wystąpił problem z uzyskaniem prognozy pogody.",
                )

        return AgentResponse(
            success=False,
            error="Nieprawidłowy format danych wejściowych.",
            text="Przepraszam, nie mogłem przetworzyć tego zapytania o pogodę.",
        )

    async def _extract_location(self, query: str) -> str:
        """Extract location from user query using LLM"""
        prompt = (
            f"Przeanalizuj poniższe zapytanie i wyodrębnij nazwę lokalizacji (miasto, kraj itp.):\n\n"
            f"Zapytanie: '{query}'\n\n"
            f"Zwróć tylko nazwę lokalizacji, bez dodatkowego tekstu. Jeśli nie ma lokalizacji, zwróć 'Warszawa'."
        )

        try:
            response = await llm_client.chat(
                model="gemma3:12b",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który ekstrahuje lokalizacje z tekstu.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not response.get("message"):
                return "Warszawa"  # Default to Warsaw if extraction fails

            location = response["message"]["content"].strip()
            return location
        except Exception as e:
            logger.error(f"Error extracting location: {e}")
            return "Warszawa"  # Default to Warsaw

    async def _fetch_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather data from the API"""
        # In a real implementation, we would call a weather API
        # This is a mockup implementation
        try:
            # Simulating API call - in reality, would use:
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(f"{self.base_url}/forecast.json",
            #                               params={"key": self.api_key, "q": location, "days": 3})

            # For demo purposes, return mock data
            mock_weather = {
                "location": {
                    "name": location,
                    "country": (
                        "Poland"
                        if location in ["Warszawa", "Kraków", "Gdańsk"]
                        else "Unknown"
                    ),
                },
                "current": {
                    "temp_c": 22,
                    "condition": {
                        "text": "Partly cloudy",
                        "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                    },
                    "wind_kph": 15,
                    "humidity": 65,
                },
                "forecast": {
                    "forecastday": [
                        {
                            "date": "2025-06-15",
                            "day": {
                                "maxtemp_c": 24,
                                "mintemp_c": 16,
                                "condition": {
                                    "text": "Partly cloudy",
                                    "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                                },
                            },
                        },
                        {
                            "date": "2025-06-16",
                            "day": {
                                "maxtemp_c": 26,
                                "mintemp_c": 17,
                                "condition": {
                                    "text": "Sunny",
                                    "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                                },
                            },
                        },
                    ]
                },
            }
            return mock_weather
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return {}

    async def _format_weather_response(
        self, location: str, weather_data: Dict[str, Any]
    ) -> str:
        """Format weather data into a user-friendly response using LLM"""
        # Extract relevant weather information
        try:
            current = weather_data.get("current", {})
            forecast = weather_data.get("forecast", {}).get("forecastday", [])

            current_temp = current.get("temp_c", "N/A")
            current_condition = current.get("condition", {}).get("text", "N/A")
            current_wind = current.get("wind_kph", "N/A")
            current_humidity = current.get("humidity", "N/A")

            # Create a summary for the LLM
            weather_summary = (
                f"Lokalizacja: {location}\n"
                f"Aktualna temperatura: {current_temp}°C\n"
                f"Warunki: {current_condition}\n"
                f"Wiatr: {current_wind} km/h\n"
                f"Wilgotność: {current_humidity}%\n\n"
            )

            if forecast:
                weather_summary += "Prognoza na najbliższe dni:\n"
                for day in forecast:
                    date = day.get("date", "N/A")
                    max_temp = day.get("day", {}).get("maxtemp_c", "N/A")
                    min_temp = day.get("day", {}).get("mintemp_c", "N/A")
                    condition = (
                        day.get("day", {}).get("condition", {}).get("text", "N/A")
                    )
                    weather_summary += (
                        f"- {date}: {min_temp}°C to {max_temp}°C, {condition}\n"
                    )

            # Let the LLM format this into a nice response
            prompt = (
                f"Na podstawie poniższych danych pogodowych, utwórz przyjazną i naturalnie brzmiącą "
                f"prognozę pogody w języku polskim:\n\n{weather_summary}"
            )

            response = await llm_client.chat(
                model="gemma3:12b",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem pogodowym.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not response.get("message"):
                return weather_summary

            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Error formatting weather response: {e}")
            return f"Aktualna temperatura w {location} wynosi {weather_data.get('current', {}).get('temp_c', 'N/A')}°C."
