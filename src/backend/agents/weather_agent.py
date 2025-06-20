import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, ConfigDict, Field

from ..config import settings
from ..core.cache_manager import cache_manager
from ..core.decorators import handle_exceptions
from ..core.exceptions import ConfigurationError, NetworkError
from ..core.hybrid_llm_client import hybrid_llm_client
from .base_agent import BaseAgent
from .interfaces import AgentResponse

logger = logging.getLogger(__name__)

# Constants
WEATHER_ALERT_LEVELS = {
    "warning": 3,  # Highest severity
    "watch": 2,  # Moderate severity
    "advisory": 1,  # Low severity
}


class WeatherProvider(BaseModel):
    """Model for a weather data provider configuration"""

    name: str
    api_key_env_var: str
    base_url: str
    api_key: Optional[str] = None
    is_enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    last_error: Optional[str] = None
    error_count: int = 0
    last_success: Optional[datetime] = None


class WeatherRequest(BaseModel):
    """Model for weather request parameters"""

    location: str
    days: int = Field(default=3, ge=1, le=7)
    include_alerts: bool = True
    model: str = "gemma3:12b"  # Użyj domyślnego modelu


class WeatherAlert(BaseModel):
    """Model for weather alerts"""

    event: str  # Type of alert (e.g., "Thunderstorm Warning")
    severity: int  # 1-3 scale, 3 being most severe
    headline: str  # Short description
    description: Optional[str] = None  # Detailed description
    effective: Optional[datetime] = None  # When alert starts
    expires: Optional[datetime] = None  # When alert ends
    areas: List[str] = []  # Affected areas


class WeatherData(BaseModel):
    """Model for standardized weather data across providers"""

    location: str
    current: Dict[str, Any]
    forecast: List[Dict[str, Any]]
    alerts: List[WeatherAlert] = []
    provider: str
    last_updated: datetime = Field(default_factory=datetime.now)


class WeatherAgent(BaseAgent):
    """Weather agent with multi-provider fallback and alert handling"""

    def __init__(
        self,
        name: str = "WeatherAgent",
        error_handler=None,
        fallback_manager=None,
        alert_service=None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            error_handler=error_handler,
            fallback_manager=fallback_manager,
        )
        self.input_model = WeatherRequest
        self.providers: List[WeatherProvider] = self._init_providers()
        self.http_client = httpx.AsyncClient(
            timeout=10.0, headers={"User-Agent": settings.USER_AGENT}
        )
        self.cache: Dict[str, Tuple[WeatherData, datetime]] = {}
        self.cache_ttl = timedelta(minutes=15)  # Cache weather data for 15 minutes
        self.llm_client = hybrid_llm_client  # Dodaję atrybut llm_client dla testów
        self.weather_service = self  # Dodaję atrybut weather_service dla testów

    def _init_providers(self) -> List[WeatherProvider]:
        """Initialize weather data providers"""
        providers = [
            WeatherProvider(
                name="weatherapi",
                api_key_env_var="WEATHER_API_KEY",
                base_url="https://api.weatherapi.com/v1",
                priority=1,
            ),
            WeatherProvider(
                name="openweathermap",
                api_key_env_var="OPENWEATHER_API_KEY",
                base_url="https://api.openweathermap.org/data/2.5",
                priority=2,
            ),
        ]

        # Populate API keys from environment variables
        for provider in providers:
            if provider.api_key_env_var == "WEATHER_API_KEY":
                provider.api_key = settings.WEATHER_API_KEY
            elif provider.api_key_env_var == "OPENWEATHER_API_KEY":
                provider.api_key = settings.OPENWEATHER_API_KEY
            else:
                provider.api_key = os.environ.get(provider.api_key_env_var)

            if not provider.api_key:
                provider.is_enabled = False
                logger.warning(f"No API key found for {provider.name}, disabling")

        return sorted(providers, key=lambda p: p.priority)

    @handle_exceptions(max_retries=2)
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process a weather forecast request with provider fallback"""
        try:
            # Extract query from input data
            query = input_data.get("query", "")
            use_bielik = input_data.get("use_bielik", True)
            model = (
                "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
                if use_bielik
                else "gemma3:12b"
            )
            include_alerts = input_data.get("include_alerts", True)

            # Extract location from query if not provided
            location = input_data.get("location", "")
            if not location and query:
                location = await self._extract_location(query, model)

            # If still no location, use default
            if not location:
                location = "Warszawa"

            logger.info(
                f"Processing weather request for location: {location}, model: {model}"
            )

            # Check cache first
            cache_key = f"{location}_{include_alerts}"
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                logger.info(f"Using cached weather data for {location}")
                return self._format_response(cached_data, model)

            # Try each provider until success
            weather_data = None
            for provider in self.providers:
                if not provider.is_enabled:
                    continue

                try:
                    logger.info(
                        f"Fetching weather data for {location} from {provider.name}"
                    )
                    if provider.name == "weatherapi":
                        weather_data = await self._fetch_weatherapi(
                            location, 3, include_alerts
                        )
                    elif provider.name == "openweathermap":
                        weather_data = await self._fetch_openweathermap(
                            location, 3, include_alerts
                        )

                    if weather_data:
                        # Update provider stats
                        provider.last_success = datetime.now()
                        provider.last_error = None

                        # Cache successful result
                        await self._add_to_cache(cache_key, weather_data)
                        break

                except Exception as e:
                    logger.error(f"Error with provider {provider.name}: {str(e)}")
                    provider.last_error = str(e)
                    provider.error_count += 1

            # Check if we got data from any provider
            if not weather_data:
                # Return a helpful response even without API data
                return AgentResponse(
                    success=True,
                    text=f"Przepraszam, nie mogę obecnie pobrać aktualnej prognozy pogody dla {location}. "
                    f"Sprawdź lokalne źródła pogodowe lub spróbuj ponownie później.",
                    data={"location": location, "error": "No weather data available"},
                )

            # Check for severe weather alerts
            has_severe_alerts = any(
                alert.severity >= 2 for alert in weather_data.alerts
            )

            # Format response with LLM
            return self._format_response(weather_data, model, has_severe_alerts)

        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, error: Exception) -> AgentResponse:
        """Handle errors in weather processing"""
        error_message = str(error)
        logger.error(f"Weather agent error: {error_message}")

        return AgentResponse(
            success=False,
            error=error_message,
            text=f"Przepraszam, wystąpił błąd podczas pobierania informacji o pogodzie: {error_message}",
        )

    async def _extract_location(self, query: str, model: str) -> str:
        """Extract location from user query using LLM"""
        prompt = (
            f"Przeanalizuj poniższe zapytanie i wyodrębnij nazwę miasta lub lokalizacji:\n\n"
            f"Zapytanie: '{query}'\n\n"
            f"Zwróć tylko nazwę miasta/lokalizacji, bez dodatkowego tekstu."
        )

        try:
            response = await hybrid_llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który wyodrębnia nazwy miast z zapytań o pogodę.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if response and response.get("message"):
                location = response["message"]["content"].strip()
                logger.info(f"Extracted location: {location}")
                return location
            else:
                return "Warszawa"  # Default fallback

        except Exception as e:
            logger.error(f"Error extracting location: {e}")
            return "Warszawa"  # Default fallback

    async def _fetch_weatherapi(
        self, location: str, days: int = 3, include_alerts: bool = True
    ) -> Optional[WeatherData]:
        """Fetch weather data from WeatherAPI.com"""
        provider = next(p for p in self.providers if p.name == "weatherapi")

        if not provider.api_key:
            return None

        try:
            url = f"{provider.base_url}/forecast.json"
            params = {
                "key": provider.api_key,
                "q": location,
                "days": days,
                "aqi": "no",
                "alerts": "yes" if include_alerts else "no",
            }

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse current weather
            current = data.get("current", {})
            current_weather = {
                "temp_c": current.get("temp_c"),
                "feelslike_c": current.get("feelslike_c"),
                "humidity": current.get("humidity"),
                "pressure_mb": current.get("pressure_mb"),
                "wind_kph": current.get("wind_kph"),
                "wind_dir": current.get("wind_dir"),
                "condition": current.get("condition", {}).get("text"),
                "uv": current.get("uv"),
            }

            # Parse forecast
            forecast = []
            for day in data.get("forecast", {}).get("forecastday", []):
                day_data = {
                    "date": day.get("date"),
                    "max_temp_c": day.get("day", {}).get("maxtemp_c"),
                    "min_temp_c": day.get("day", {}).get("mintemp_c"),
                    "condition": day.get("day", {}).get("condition", {}).get("text"),
                    "chance_of_rain": day.get("day", {}).get("daily_chance_of_rain"),
                }
                forecast.append(day_data)

            # Parse alerts
            alerts = []
            for alert_data in data.get("alerts", {}).get("alert", []):
                alert = WeatherAlert(
                    event=alert_data.get("event", ""),
                    severity=WEATHER_ALERT_LEVELS.get(
                        alert_data.get("severity", "advisory"), 1
                    ),
                    headline=alert_data.get("headline", ""),
                    description=alert_data.get("desc"),
                    effective=datetime.fromisoformat(
                        alert_data.get("effective", "").replace("Z", "+00:00")
                    ),
                    expires=datetime.fromisoformat(
                        alert_data.get("expires", "").replace("Z", "+00:00")
                    ),
                    areas=alert_data.get("areas", []),
                )
                alerts.append(alert)

            return WeatherData(
                location=data.get("location", {}).get("name", location),
                current=current_weather,
                forecast=forecast,
                alerts=alerts,
                provider="weatherapi",
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error(
                    f"WeatherAPI authentication failed (401): Invalid API key for {provider.name}"
                )
                provider.is_enabled = False
                provider.last_error = "Invalid API key - provider disabled"
                raise ConfigurationError(
                    f"Invalid API key for {provider.name}",
                    config_key=provider.api_key_env_var,
                    details={"status_code": 401, "provider": provider.name},
                )
            elif e.response.status_code == 429:
                logger.warning(
                    f"WeatherAPI rate limit exceeded (429) for {provider.name}"
                )
                raise NetworkError(
                    f"Rate limit exceeded for {provider.name}",
                    url=url,
                    status_code=429,
                    details={
                        "provider": provider.name,
                        "retry_after": e.response.headers.get("Retry-After"),
                    },
                )
            else:
                logger.error(
                    f"WeatherAPI HTTP error {e.response.status_code} for {provider.name}: {e}"
                )
                raise NetworkError(
                    f"HTTP error {e.response.status_code} from {provider.name}",
                    url=url,
                    status_code=e.response.status_code,
                    details={"provider": provider.name},
                )
        except httpx.RequestError as e:
            logger.error(f"Network error with {provider.name}: {e}")
            raise NetworkError(
                f"Network error with {provider.name}",
                url=url,
                details={"provider": provider.name, "error": str(e)},
            )
        except Exception as e:
            logger.error(f"Error fetching from WeatherAPI: {e}")
            return None

    async def _fetch_openweathermap(
        self, location: str, days: int = 3, include_alerts: bool = True
    ) -> Optional[WeatherData]:
        """Fetch weather data from OpenWeatherMap API"""
        provider = next(p for p in self.providers if p.name == "openweathermap")

        if not provider.api_key:
            return None

        try:
            # Get current weather
            current_url = f"{provider.base_url}/weather"
            current_params = {
                "q": location,
                "appid": provider.api_key,
                "units": "metric",
                "lang": "pl",
            }

            current_response = await self.http_client.get(
                current_url, params=current_params
            )
            current_response.raise_for_status()
            current_data = current_response.json()

            # Parse current weather
            current_weather = {
                "temp_c": current_data.get("main", {}).get("temp"),
                "feelslike_c": current_data.get("main", {}).get("feels_like"),
                "humidity": current_data.get("main", {}).get("humidity"),
                "pressure_mb": current_data.get("main", {}).get("pressure"),
                "wind_kph": current_data.get("wind", {}).get("speed"),
                "wind_dir": self._get_wind_direction(
                    current_data.get("wind", {}).get("deg", 0)
                ),
                "condition": current_data.get("weather", [{}])[0].get("description"),
                "uv": None,  # OpenWeatherMap doesn't provide UV in free tier
            }

            # Get forecast (5-day)
            forecast_url = f"{provider.base_url}/forecast"
            forecast_params = {
                "q": location,
                "appid": provider.api_key,
                "units": "metric",
                "lang": "pl",
            }

            forecast_response = await self.http_client.get(
                forecast_url, params=forecast_params
            )
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Parse forecast (daily averages)
            forecast = []
            daily_data = {}

            for item in forecast_data.get("list", []):
                date = item.get("dt_txt", "").split(" ")[0]
                if date not in daily_data:
                    daily_data[date] = {
                        "temps": [],
                        "conditions": [],
                        "chance_of_rain": [],
                    }

                daily_data[date]["temps"].append(item.get("main", {}).get("temp"))
                daily_data[date]["conditions"].append(
                    item.get("weather", [{}])[0].get("description")
                )
                daily_data[date]["chance_of_rain"].append(item.get("pop", 0) * 100)

            for date, data in list(daily_data.items())[:days]:
                if data["temps"]:
                    day_forecast = {
                        "date": date,
                        "max_temp_c": max(data["temps"]),
                        "min_temp_c": min(data["temps"]),
                        "condition": max(
                            set(data["conditions"]), key=data["conditions"].count
                        ),
                        "chance_of_rain": max(data["chance_of_rain"]),
                    }
                    forecast.append(day_forecast)

            return WeatherData(
                location=current_data.get("name", location),
                current=current_weather,
                forecast=forecast,
                alerts=[],  # OpenWeatherMap doesn't provide alerts in free tier
                provider="openweathermap",
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error(
                    f"OpenWeatherMap authentication failed (401): Invalid API key for {provider.name}"
                )
                provider.is_enabled = False
                provider.last_error = "Invalid API key - provider disabled"
                raise ConfigurationError(
                    f"Invalid API key for {provider.name}",
                    config_key=provider.api_key_env_var,
                    details={"status_code": 401, "provider": provider.name},
                )
            elif e.response.status_code == 429:
                logger.warning(
                    f"OpenWeatherMap rate limit exceeded (429) for {provider.name}"
                )
                raise NetworkError(
                    f"Rate limit exceeded for {provider.name}",
                    url=current_url,
                    status_code=429,
                    details={
                        "provider": provider.name,
                        "retry_after": e.response.headers.get("Retry-After"),
                    },
                )
            else:
                logger.error(
                    f"OpenWeatherMap HTTP error {e.response.status_code} for {provider.name}: {e}"
                )
                raise NetworkError(
                    f"HTTP error {e.response.status_code} from {provider.name}",
                    url=current_url,
                    status_code=e.response.status_code,
                    details={"provider": provider.name},
                )
        except httpx.RequestError as e:
            logger.error(f"Network error with {provider.name}: {e}")
            raise NetworkError(
                f"Network error with {provider.name}",
                url=current_url,
                details={"provider": provider.name, "error": str(e)},
            )
        except Exception as e:
            logger.error(f"Error fetching from OpenWeatherMap: {e}")
            return None

    def _get_wind_direction(self, degrees: float) -> str:
        """Convert wind direction from degrees to text"""
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]

        if degrees < 0:
            degrees += 360

        index = round(degrees / 22.5) % 16
        return directions[index]

    async def _get_from_cache(self, cache_key: str) -> Optional[WeatherData]:
        """Get weather data from cache if not expired"""
        try:
            cached_data = await cache_manager.get(f"weather:{cache_key}")
            if cached_data:
                logger.info(f"Using cached weather data for {cache_key}")
                return WeatherData(**cached_data)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def _add_to_cache(self, cache_key: str, data: WeatherData) -> None:
        """Add weather data to cache"""
        try:
            await cache_manager.set(
                f"weather:{cache_key}", data.model_dump(), ttl=900
            )  # 15 minutes
            logger.debug(f"Added weather data to cache: {cache_key}")
        except Exception as e:
            logger.error(f"Error adding to cache: {e}")

    def _format_response(
        self, weather_data: WeatherData, model: str, has_severe_alerts: bool = False
    ) -> AgentResponse:
        """Format weather data into a natural language response"""
        try:
            # Create a summary of weather data
            current = weather_data.current
            forecast = weather_data.forecast

            weather_summary = f"""
            Lokalizacja: {weather_data.location}

            Aktualna pogoda:
            - Temperatura: {current.get('temp_c')}°C
            - Odczuwalna: {current.get('feelslike_c')}°C
            - Wilgotność: {current.get('humidity')}%
            - Wiatr: {current.get('wind_kph')} km/h, {current.get('wind_dir')}
            - Opis: {current.get('condition')}

            Prognoza na najbliższe dni:
            """

            for day in forecast[:3]:  # Show next 3 days
                weather_summary += f"""
            {day.get('date')}:
            - Maksymalna: {day.get('max_temp_c')}°C
            - Minimalna: {day.get('min_temp_c')}°C
            - Opis: {day.get('condition')}
            - Szansa deszczu: {day.get('chance_of_rain')}%
            """

            if weather_data.alerts:
                weather_summary += "\n\nOstrzeżenia pogodowe:\n"
                for alert in weather_data.alerts:
                    weather_summary += f"- {alert.headline}\n"

            # Use LLM to format the response naturally
            prompt = f"""
            Przedstaw informacje o pogodzie w sposób naturalny i przyjazny dla użytkownika.

            {weather_summary}

            Przedstaw te informacje w sposób naturalny, jakbyś rozmawiał z przyjacielem.
            Jeśli są ostrzeżenia pogodowe, zwróć na nie szczególną uwagę.
            """

            # For now, return formatted text directly
            # In a full implementation, you would use the LLM here
            formatted_text = self._format_weather_text(
                weather_summary, has_severe_alerts
            )

            return AgentResponse(
                success=True,
                text=formatted_text,
                data={
                    "location": weather_data.location,
                    "current": current,
                    "forecast": forecast,
                    "alerts": [alert.dict() for alert in weather_data.alerts],
                    "provider": weather_data.provider,
                },
            )

        except Exception as e:
            logger.error(f"Error formatting weather response: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                text="Przepraszam, wystąpił błąd podczas formatowania odpowiedzi o pogodzie.",
            )

    def _format_weather_text(
        self, weather_summary: str, has_severe_alerts: bool
    ) -> str:
        """Format weather summary into natural language"""
        lines = weather_summary.strip().split("\n")
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if line.startswith("Lokalizacja:"):
                formatted_lines.append(f"📍 {line}")
            elif line.startswith("Aktualna pogoda:"):
                formatted_lines.append(f"\n🌤️ {line}")
            elif line.startswith("- Temperatura:"):
                formatted_lines.append(f"🌡️ {line}")
            elif line.startswith("- Odczuwalna:"):
                formatted_lines.append(f"🌡️ {line}")
            elif line.startswith("- Wilgotność:"):
                formatted_lines.append(f"💧 {line}")
            elif line.startswith("- Wiatr:"):
                formatted_lines.append(f"🌪️ {line}")
            elif line.startswith("- Opis:"):
                formatted_lines.append(f"☁️ {line}")
            elif line.startswith("Prognoza na najbliższe dni:"):
                formatted_lines.append(f"\n📅 {line}")
            elif line.startswith("Ostrzeżenia pogodowe:"):
                formatted_lines.append(f"\n⚠️ {line}")
            elif line and not line.startswith("-"):
                formatted_lines.append(line)
            elif line.startswith("-"):
                formatted_lines.append(f"  {line}")

        text = "\n".join(formatted_lines)

        if has_severe_alerts:
            text += "\n\n⚠️ UWAGA: Aktywne są ostrzeżenia pogodowe! Sprawdź lokalne źródła informacji."

        return text

    async def _stream_weather_response(
        self, model: str, prompt: str
    ) -> AsyncGenerator[str, None]:
        """Stream weather response using LLM"""
        try:
            response_stream = await hybrid_llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem pogodowym. Przedstaw informacje o pogodzie w sposób naturalny i przyjazny.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            async for chunk in response_stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except Exception as e:
            logger.error(f"Error streaming weather response: {e}")
            yield "Przepraszam, wystąpił błąd podczas generowania odpowiedzi o pogodzie."

    async def close(self) -> None:
        """Close HTTP client"""
        await self.http_client.aclose()

    @handle_exceptions(max_retries=1)
    def get_dependencies(self) -> list[str]:
        """Return list of dependencies this agent requires"""
        return ["httpx", "hybrid_llm_client"]

    def get_metadata(self) -> dict:
        """Return metadata about this agent"""
        return {
            "name": self.name,
            "description": "Agent that provides weather information with multi-provider support",
            "version": "1.0.0",
            "capabilities": [
                "weather_forecast",
                "location_search",
                "alert_monitoring",
                "multi_provider_fallback",
            ],
        }

    def is_healthy(self) -> bool:
        """Check if the agent is healthy and ready to process requests"""
        return any(provider.is_enabled for provider in self.providers)
