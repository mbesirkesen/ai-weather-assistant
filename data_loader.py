"""Download and prepare OpenWeatherMap API documentation for RAG."""
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def scrape_openweathermap_docs():
    """
    Scrape OpenWeatherMap API documentation.
    Returns a list of documentation sections.
    """
    sections = []
    
    # OpenWeatherMap API documentation URLs
    doc_urls = [
        "https://openweathermap.org/api",  # Main API page
        "https://openweathermap.org/api/current",  # Current weather API
        "https://openweathermap.org/api/weathermap",  # Weather maps
        "https://openweathermap.org/appid",  # API key information
        "https://openweathermap.org/guide",  # General guide
    ]
    
    for url in doc_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract main content
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up whitespace
                lines = [line.strip() for line in text.splitlines()]
                text = '\n'.join([line for line in lines if line])
                
                sections.append(f"Documentation from {url}:\n\n{text}\n\n")
                logger.info(f"Successfully scraped {url}")
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
    
    return sections


def get_fallback_documentation():
    """
    Fallback documentation in case web scraping fails.
    Returns essential OpenWeatherMap API information.
    """
    return [
        """
        OpenWeatherMap API Documentation
        
        Getting an API Key:
        To use OpenWeatherMap API, you need to sign up at openweathermap.org and get a free API key.
        The API key should be included in all API requests as the 'appid' parameter.
        Free tier allows 60 calls per minute.
        
        Current Weather Data Endpoint:
        The main endpoint for current weather data is:
        api.openweathermap.org/data/2.5/weather
        
        Parameters:
        - q: City name, state code and country code divided by comma (e.g., "London,uk")
        - appid: Your unique API key
        - units: Units of measurement (standard, metric, imperial)
        - lang: Language for weather descriptions
        
        Example Request:
        GET https://api.openweathermap.org/data/2.5/weather?q=London,uk&appid=YOUR_API_KEY&units=metric
        
        Response Format:
        The API returns JSON with the following main fields:
        - main: Contains temperature, pressure, humidity
        - weather: Array with weather condition info
        - wind: Wind speed and direction
        - clouds: Cloud coverage
        - name: City name
        
        Common Weather Endpoints:
        - Current Weather: /weather
        - 5 Day Forecast: /forecast
        - Hourly Forecast (16 days): /forecast/hourly
        - Historical Data: /onecall/timemachine
        - Weather Maps: /map layers
        
        Rate Limits:
        Free plan: 60 calls/minute, 1,000,000 calls/month
        Subscription plans have higher limits.
        
        Error Codes:
        - 401: Invalid API key
        - 404: City not found
        - 429: Too many requests
        """,
        """
        API Key Management:
        
        How to get an API key:
        1. Sign up at openweathermap.org
        2. Verify your email
        3. Navigate to API keys section
        4. Generate a new key or use the default key
        
        Security:
        - Never share your API key publicly
        - Store API keys in environment variables
        - Use HTTPS for all API requests
        - Monitor your API usage
        
        Pricing Tiers:
        - Free: Limited features, 60 calls/min
        - Startup: More features, higher limits
        - Developer: Full access
        - Professional: Enterprise features
        """,
        """
        Current Weather Endpoint Details:
        
        Endpoint: /weather
        Method: GET
        Base URL: api.openweathermap.org/data/2.5
        
        Required Parameters:
        - appid: Your API key
        
        Optional Parameters:
        - q: City name (or city,country code)
        - lat/lon: Geographic coordinates
        - zip: Zip code,country code
        - id: City ID
        - units: Temperature units (default: Kelvin, metric: Celsius, imperial: Fahrenheit)
        - lang: Language code
        
        Example Responses:
        Temperature values are in specified units.
        Weather conditions include codes and descriptions.
        Wind speed is in m/s.
        Pressure is in hPa.
        
        Use Cases:
        - Real-time weather monitoring
        - Weather dashboards
        - Mobile applications
        - IoT devices
        """
    ]


def load_documentation():
    """
    Load OpenWeatherMap documentation for RAG.
    First tries to scrape, falls back to static documentation.
    """
    try:
        sections = scrape_openweathermap_docs()
        if sections:
            logger.info(f"Successfully loaded {len(sections)} documentation sections from web")
            return sections
    except Exception as e:
        logger.warning(f"Failed to scrape documentation: {e}")
    
    # Fallback to static documentation
    fallback_docs = get_fallback_documentation()
    logger.info(f"Using fallback documentation ({len(fallback_docs)} sections)")
    return fallback_docs

