"""OpenWeatherMap API integration for fetching live weather data."""
import requests
from config import Config
import logging

logger = logging.getLogger(__name__)


class WeatherAPI:
    """Interface to OpenWeatherMap API."""
    
    def __init__(self):
        """Initialize the Weather API client."""
        self.api_key = Config.OPENWEATHERMAP_API_KEY
        self.base_url = Config.OPENWEATHERMAP_BASE_URL
    
    def get_current_weather(self, city, country_code=None, units="metric"):
        """
        Fetch current weather for a specific city.
        
        Args:
            city: City name (e.g., "Istanbul")
            country_code: Optional country code (e.g., "TR")
            units: Temperature units (metric, imperial, or standard)
            
        Returns:
            Dict with weather data or None if error
        """
        try:
            query = city
            if country_code:
                query = f"{city},{country_code}"
            
            url = f"{self.base_url}/weather"
            params = {
                "q": query,
                "appid": self.api_key,
                "units": units,
                "lang": "en"  # English descriptions
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched weather for {city}")
                return self._format_weather_data(data)
            elif response.status_code == 401:
                logger.error("Invalid API key")
                return {"error": "Invalid API key. Please check your OpenWeatherMap API key."}
            elif response.status_code == 404:
                logger.warning(f"City not found: {city}")
                return {"error": f"City '{city}' not found. Please check the city name."}
            elif response.status_code == 429:
                logger.error("Rate limit exceeded")
                return {"error": "API rate limit exceeded. Please try again later."}
            else:
                logger.error(f"API error: {response.status_code}")
                return {"error": f"Weather API error: {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return {"error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_multiple_cities_weather(self, cities_list, units="metric"):
        """
        Fetch weather for multiple cities.
        
        Args:
            cities_list: List of city names or tuples (city, country_code)
            units: Temperature units
            
        Returns:
            Dict with weather data for each city
        """
        results = {}
        
        for city_input in cities_list:
            if isinstance(city_input, tuple):
                city, country_code = city_input
            else:
                city = city_input
                country_code = None
            
            weather = self.get_current_weather(city, country_code, units)
            results[city] = weather
        
        return results
    
    def _format_weather_data(self, data):
        """
        Format raw API response into a user-friendly format.
        
        Args:
            data: Raw API response JSON
            
        Returns:
            Formatted dictionary
        """
        try:
            formatted = {
                "city": data.get("name", "Unknown"),
                "country": data.get("sys", {}).get("country", ""),
                "temperature": data.get("main", {}).get("temp", 0),
                "feels_like": data.get("main", {}).get("feels_like", 0),
                "humidity": data.get("main", {}).get("humidity", 0),
                "pressure": data.get("main", {}).get("pressure", 0),
                "description": data.get("weather", [{}])[0].get("description", "N/A").title(),
                "wind_speed": data.get("wind", {}).get("speed", 0),
                "wind_direction": data.get("wind", {}).get("deg", 0),
                "clouds": data.get("clouds", {}).get("all", 0),
                "visibility": data.get("visibility", 0) / 1000 if data.get("visibility") else None,
                "timestamp": data.get("dt", 0)
            }
            
            # Add wind direction description
            if formatted["wind_direction"]:
                formatted["wind_direction_desc"] = self._get_wind_direction(
                    formatted["wind_direction"]
                )
            
            return formatted
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return {"error": f"Error processing weather data: {str(e)}"}
    
    def _get_wind_direction(self, degrees):
        """Convert wind direction from degrees to cardinal direction."""
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def check_api_health(self):
        """Check if the API key is valid by making a test request."""
        try:
            # Test with a well-known city
            result = self.get_current_weather("London", "uk")
            return "error" not in result
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False

