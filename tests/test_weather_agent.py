import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.weather_agent import WeatherAgent
from backend.agents.interfaces import AgentResponse

@pytest.mark.asyncio
async def test_weather_agent_current_weather():
    """Test weather agent for current weather requests"""
    agent = WeatherAgent()
    
    # Mock the _extract_location method
    with patch.object(agent, "_extract_location") as mock_extract:
        mock_extract.return_value = "Warszawa"
        
        # Mock the weather API call
        with patch.object(agent, "_fetch_weatherapi") as mock_fetch:
            mock_weather_data = MagicMock()
            mock_weather_data.current = MagicMock(
                temp_c=22.5,
                condition=MagicMock(text="Sunny"),
                humidity=45,
                wind_kph=10.5,
            )
            mock_weather_data.location = MagicMock(
                name="Warsaw",
                country="Poland",
            )
            mock_weather_data.forecast = None
            mock_weather_data.alerts = []
            mock_fetch.return_value = mock_weather_data
            
            # Process a weather request
            result = await agent.process({
                "query": "jaka jest dzisiaj pogoda w Warszawie?",
                "model": "gemma3:12b",
            })
            
            # Verify the result
            assert result.success is True
            assert "Warszawa" in result.text
            assert "22.5" in result.text
            assert "Sunny" in result.text

@pytest.mark.asyncio
async def test_weather_agent_future_date():
    """Test weather agent for future date forecasts"""
    agent = WeatherAgent()
    
    # Mock the _extract_location method
    with patch.object(agent, "_extract_location") as mock_extract:
        mock_extract.return_value = "Warszawa"
        
        # Mock the _extract_date method
        with patch.object(agent, "_extract_date") as mock_date:
            # Set the date to 2025-06-28 from the user query
            future_date = datetime(2025, 6, 28, 12, 0, 0)
            mock_date.return_value = future_date
            
            # Mock the weather API call
            with patch.object(agent, "_fetch_weatherapi") as mock_fetch:
                mock_forecast_day = MagicMock(
                    date=future_date.strftime("%Y-%m-%d"),
                    day=MagicMock(
                        avgtemp_c=25.0,
                        condition=MagicMock(text="Partly cloudy"),
                        maxtemp_c=30.0,
                        mintemp_c=20.0,
                        daily_chance_of_rain=30,
                    )
                )
                
                mock_weather_data = MagicMock()
                mock_weather_data.forecast = MagicMock(
                    forecastday=[mock_forecast_day]
                )
                mock_weather_data.location = MagicMock(
                    name="Warsaw",
                    country="Poland",
                )
                mock_weather_data.alerts = []
                mock_fetch.return_value = mock_weather_data
                
                # Process a weather request with future date
                result = await agent.process({
                    "query": "Jaka będzie pogoda w Warszawie 28 czerwca 2025 roku?",
                    "model": "gemma3:12b",
                })
                
                # Verify the result
                assert result.success is True
                assert "28 czerwca 2025" in result.text
                assert "Warszawa" in result.text
                assert "25.0" in result.text or "25°C" in result.text
                assert "Partly cloudy" in result.text or "Częściowe zachmurzenie" in result.text

@pytest.mark.asyncio
async def test_weather_agent_location_extraction():
    """Test the location extraction from query"""
    agent = WeatherAgent()
    
    # Test with direct location name
    query1 = "Jaka jest pogoda w Krakowie?"
    location1 = await agent._extract_location(query1)
    assert location1 == "Kraków"
    
    # Test with unusual city name
    query2 = "Pogoda w Ząbkach na jutro"
    location2 = await agent._extract_location(query2)
    assert location2 == "Ząbki"
    
    # Test default location when none provided
    query3 = "Jaka jest dzisiejsza pogoda?"
    with patch("backend.config.settings.DEFAULT_LOCATION", "Warszawa"):
        location3 = await agent._extract_location(query3)
        assert location3 == "Warszawa"

@pytest.mark.asyncio
async def test_weather_agent_date_extraction():
    """Test date extraction from weather queries"""
    agent = WeatherAgent()
    today = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    tomorrow = (today + timedelta(days=1))
    
    # Test with "tomorrow" keyword
    with patch("backend.agents.tools.date_parser.parse_relative_date") as mock_parse:
        mock_parse.return_value = tomorrow
        query1 = "Jaka będzie jutro pogoda?"
        date1 = await agent._extract_date(query1)
        assert date1.date() == tomorrow.date()
    
    # Test with specific date
    with patch("backend.agents.tools.date_parser.parse_date") as mock_parse:
        future_date = datetime(2025, 6, 28, 12, 0, 0)
        mock_parse.return_value = future_date
        query2 = "Jaka będzie pogoda 28 czerwca 2025?"
        date2 = await agent._extract_date(query2)
        assert date2.date() == future_date.date()
    
    # Test default to today when no date in query
    query3 = "Jaka jest pogoda w Warszawie?"
    date3 = await agent._extract_date(query3)
    assert date3.date() == today.date()
    
@pytest.mark.asyncio
async def test_weather_agent_multiple_locations():
    """Test handling multiple locations in a query"""
    agent = WeatherAgent()
    
    # Mock the weather API call for comparison query
    with patch.object(agent, "_fetch_weatherapi") as mock_fetch:
        mock_weather_data_warsaw = MagicMock()
        mock_weather_data_warsaw.current = MagicMock(
            temp_c=22.0,
            condition=MagicMock(text="Sunny"),
        )
        mock_weather_data_warsaw.location = MagicMock(name="Warsaw")
        
        mock_weather_data_krakow = MagicMock()
        mock_weather_data_krakow.current = MagicMock(
            temp_c=20.0,
            condition=MagicMock(text="Cloudy"),
        )
        mock_weather_data_krakow.location = MagicMock(name="Krakow")
        
        # Setup fetch to return different data for different locations
        mock_fetch.side_effect = lambda location, date=None, **kwargs: (
            mock_weather_data_warsaw if location == "Warszawa" 
            else mock_weather_data_krakow
        )
        
        # Mock location extraction to return a list
        with patch.object(agent, "_extract_locations") as mock_extract_locs:
            mock_extract_locs.return_value = ["Warszawa", "Kraków"]
            
            # Process a weather comparison request
            result = await agent.process({
                "query": "Gdzie jest cieplej, w Warszawie czy Krakowie?",
                "model": "gemma3:12b",
            })
            
            # Verify the result contains information about both cities
            assert result.success is True
            assert "Warszawa" in result.text
            assert "Kraków" in result.text
            assert "22" in result.text
            assert "20" in result.text

if __name__ == "__main__":
    pytest.main(["-v", "test_weather_agent.py"]) 