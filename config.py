"""Configuration management for the AI Weather Assistant."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"
    
    # LangSmith
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-weather-assistant")
    
    # MongoDB Atlas
    MONGODB_ATLAS_URI = os.getenv("MONGODB_ATLAS_CONNECTION_STRING")
    MONGODB_DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "ai_assistant_db")
    MONGODB_COLLECTION_NAME = "weather_docs"
    
    # OpenWeatherMap
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # LangGraph
    LANGGRAPH_PORT = 20240
    
    # Memory settings
    MAX_CONTEXT_LENGTH = 4000  # Context window limit
    CONVERSATION_SUMMARY_THRESHOLD = 0.8  # When to summarize conversations
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set."""
        missing = []
        
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.OPENWEATHERMAP_API_KEY:
            missing.append("OPENWEATHERMAP_API_KEY")
        if not cls.MONGODB_ATLAS_URI:
            missing.append("MONGODB_ATLAS_CONNECTION_STRING")
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        return True

