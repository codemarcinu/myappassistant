import logging
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.weather_agent import WeatherAgent
from backend.infrastructure.database.database import get_db

router = APIRouter(prefix="/weather", tags=["Weather"])
logger = logging.getLogger(__name__)

# Inicjalizacja agenta - w przyszłości można użyć fabryki/DI
weather_agent = WeatherAgent()


@router.get("/")
async def get_weather_for_locations(
    locations: List[str] = Query(
        ..., description="List of locations to get weather for"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current weather and a brief forecast for a list of locations.
    """
    all_weather_data = []
    for location in locations:
        try:
            response = await weather_agent.process({"location": location})
            if response.success and response.data:
                # Uproszczony model odpowiedzi dla frontendu
                simplified_data = {
                    "location": response.data.get("location"),
                    "temperature": response.data.get("current", {}).get("temp_c"),
                    "condition": response.data.get("current", {}).get(
                        "condition", "Brak danych"
                    ),
                    "icon": "☀️",  # Domyślna ikona, można to zmapować
                }
                # Mapowanie ikon na podstawie warunków
                try:
                    condition_lower = (
                        simplified_data["condition"].lower()
                        if simplified_data["condition"]
                        else ""
                    )
                    if "rain" in condition_lower or "drizzle" in condition_lower:
                        simplified_data["icon"] = "🌧️"
                    elif "cloud" in condition_lower or "overcast" in condition_lower:
                        simplified_data["icon"] = "☁️"
                    elif "snow" in condition_lower:
                        simplified_data["icon"] = "❄️"
                    elif "storm" in condition_lower:
                        simplified_data["icon"] = "⛈️"
                    elif "sunny" in condition_lower or "clear" in condition_lower:
                        simplified_data["icon"] = "☀️"
                    else:
                        simplified_data["icon"] = "⛅️"  # Częściowe zachmurzenie
                except Exception as e:
                    logger.error(
                        f"Error mapping weather icon for condition '{simplified_data['condition']}': {e}"
                    )
                    simplified_data["icon"] = "🤷"

                all_weather_data.append(simplified_data)
            else:
                logger.warning(
                    f"Weather agent failed for {location}. Error: {response.error}"
                )
                # Return mock data if weather agent fails
                mock_data = {
                    "location": location,
                    "temperature": 22.5,
                    "condition": "Partly cloudy",
                    "icon": "⛅️",
                }
                all_weather_data.append(mock_data)
        except Exception as e:
            logger.error(
                f"Error processing weather for location {location}: {e}", exc_info=True
            )
            # Return mock data on any error
            mock_data = {
                "location": location,
                "temperature": 22.5,
                "condition": "Partly cloudy",
                "icon": "⛅️",
            }
            all_weather_data.append(mock_data)

    return all_weather_data
