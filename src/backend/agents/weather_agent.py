import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
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

    def __init__(self, name: str = "WeatherAgent", api_key: Optional[str] = None):
        super().__init__(name)
        self.api_key = "2488986a12e081ac677b3b2e8236dd97" or os.getenv(
            "WEATHER_API_KEY"
        )
        if not self.api_key:
            logger.warning("Weather API key not configured - using demo mode")
            self.api_key = "demo_key"
        self.base_url = "https://api.weatherapi.com/v1"

    async def process(self, input_data: Any) -> AgentResponse:
        """Process a weather forecast request"""
        if isinstance(input_data, dict):
            try:
                query = input_data.get("query", "")
                model = input_data.get("model", "gemma3:12b")  # Default model

                # Use LLM to extract location
                try:
                    location = await self._extract_location(query, model)
                    if not location:
                        return AgentResponse(
                            success=False,
                            error="Nie mogłem rozpoznać lokalizacji w zapytaniu.",
                            text="Nie mogłem rozpoznać lokalizacji w zapytaniu.",
                        )
                except Exception as e:
                    logger.error(f"Error extracting location: {str(e)}")
                    return ""
                # Remove duplicate location check

                # Fetch weather data
                weather_data = await self._fetch_weather(location)
                if not weather_data:
                    return AgentResponse(
                        success=False,
                        error=f"Nie udało się pobrać prognozy pogody dla {location}.",
                        text=f"Nie udało się pobrać prognozy pogody dla {location}.",
                    )

                # Format response with LLM, which will now be a stream
                response_stream = self._format_weather_response(
                    location, weather_data, model
                )

                # The response from the agent is now the stream itself
                api_url = "https://api.weatherapi.com/v1/forecast.json"
                params = {"key": self.api_key, "q": location, "days": 3, "lang": "pl"}

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(api_url, params=params)
                        response.raise_for_status()
                        weather_json = await response.json()

                        validated_data = {
                            "location": location,
                            "current": weather_json.get("current", {}),
                            "forecast": weather_json.get("forecast", {}).get(
                                "forecastday", []
                            ),
                        }

                        return AgentResponse(
                            success=True,
                            data=validated_data,
                            text_stream=response_stream,
                            message=f"Pogoda dla {location}",
                        )
                    except httpx.HTTPStatusError as e:
                        logger.error(f"Weather API error: {str(e)}")
                        return AgentResponse(
                            success=False,
                            error=f"Błąd API pogodowego: {str(e)}",
                            text="Przepraszam, wystąpił problem z uzyskaniem prognozy pogody.",
                        )
                    except Exception as e:
                        logger.error(f"Error processing weather response: {str(e)}")
                        return AgentResponse(
                            success=False,
                            error=f"Wystąpił błąd podczas przetwarzania odpowiedzi: {str(e)}",
                            text="Przepraszam, wystąpił problem z uzyskaniem prognozy pogody.",
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

            try:
                async for chunk in llm_client.generate_stream(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Jesteś pomocnym asystentem pogodowym.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                ):
                    content = chunk["message"]["content"]
                    yield content
            except Exception as e:
                logger.error(f"Error in weather response streaming: {e}")
                yield f"Aktualna temperatura w {location} wynosi {weather_data.get('current', {}).get('temp_c', 'N/A')}°C."
        except Exception as e:
            logger.error(f"Error formatting weather response: {e}")
            yield f"Aktualna temperatura w {location} wynosi {weather_data.get('current', {}).get('temp_c', 'N/A')}°C."
