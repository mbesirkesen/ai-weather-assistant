"""Main LangGraph agent that orchestrates RAG, API calls, and memory."""
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import operator
import logging

from config import Config
from weather_api import WeatherAPI
from vector_store import VectorStoreManager
from memory_manager import MemoryManager

logger = logging.getLogger(__name__)


# Define state for the agent
class AgentState(TypedDict):
    """State management for the LangGraph agent."""
    messages: Annotated[list, operator.add]
    next: str  # Next action to take


class WeatherAssistant:
    """Main AI assistant with RAG, weather API, and memory."""
    
    def __init__(self):
        """Initialize the weather assistant."""
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.7,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        self.weather_api = WeatherAPI()
        self.vector_store = VectorStoreManager()
        self.memory_manager = MemoryManager()
        
        # Initialize system prompt
        self.system_prompt = """You are a helpful AI weather assistant.
You have access to:
1. OpenWeatherMap API documentation (through RAG)
2. Live weather data from OpenWeatherMap API
3. Conversation history

Your capabilities:
- Answer questions about the OpenWeatherMap API (how to use it, endpoints, etc.)
- Fetch and report current weather data for any city
- Remember context from the conversation
- Provide friendly, accurate, and helpful responses

When the user asks about weather API documentation or usage, use your RAG knowledge.
When the user asks about actual weather in a city, call the weather API to get live data.

Always be concise but informative. If you don't know something, be honest about it."""
    
    def classify_intent(self, query: str) -> str:
        """
        Classify user intent to determine which tool to use.
        
        Args:
            query: User's input
            
        Returns:
            Intent: "rag", "weather_api", or "general"
        """
        classification_prompt = """Classify the user's intent based on their query.

User query: {query}

Classify as one of:
- "rag": Questions about API documentation, how to use the API, API endpoints, getting API keys, etc.
- "weather_api": Requests for actual/live weather data in specific cities
- "general": General conversation, greetings, questions about capabilities

Respond with ONLY the classification word (rag, weather_api, or general):"""

        prompt = ChatPromptTemplate.from_template(classification_prompt)
        
        try:
            response = self.llm.invoke(prompt.format_messages(query=query))
            intent = response.content.strip().lower()
            logger.info(f"Intent classified as: {intent}")
            return intent
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "general"
    
    def handle_rag_query(self, query: str) -> str:
        """
        Handle RAG-based queries about API documentation.
        
        Args:
            query: User's question about the API
            
        Returns:
            Answer based on documentation
        """
        try:
            # Search for relevant documentation
            docs = self.vector_store.similarity_search(query, k=3)
            
            if not docs:
                return "I couldn't find relevant documentation. Please try rephrasing your question."
            
            # Build context from retrieved docs
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Create RAG prompt
            rag_prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt + "\n\nUse the following documentation to answer the question:"),
                ("system", "Documentation:\n{context}"),
                ("user", "{question}")
            ])
            
            chain = rag_prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "context": context,
                "question": query
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return f"An error occurred while searching documentation: {str(e)}"
    
    def handle_weather_query(self, query: str) -> str:
        """
        Handle live weather queries.
        
        Args:
            query: User's weather request
            
        Returns:
            Weather data formatted as natural language
        """
        try:
            # Use LLM to extract city names from the query
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract city names from the user's weather query. Return ONLY the city names, separated by commas."),
                ("user", "{query}")
            ])
            
            extraction_chain = extraction_prompt | self.llm | StrOutputParser()
            cities_str = extraction_chain.invoke({"query": query})
            
            # Parse cities
            cities = [city.strip() for city in cities_str.split(",") if city.strip()]
            
            if not cities:
                return "I couldn't identify which cities you're asking about. Please specify the city name(s)."
            
            # Fetch weather for all cities
            results = {}
            for city in cities:
                weather = self.weather_api.get_current_weather(city)
                results[city] = weather
            
            # Format response
            if len(cities) == 1:
                weather = results[cities[0]]
                if "error" in weather:
                    return f"Sorry, I couldn't get weather data: {weather['error']}"
                
                response_text = f"""Current weather in {weather['city']}, {weather['country']}:

Temperature: {weather['temperature']}°C (feels like {weather['feels_like']}°C)
Condition: {weather['description']}
Humidity: {weather['humidity']}%
Wind: {weather['wind_speed']} m/s {weather.get('wind_direction_desc', '')}
Cloud coverage: {weather['clouds']}%
Pressure: {weather['pressure']} hPa"""
                
                if weather['visibility']:
                    response_text += f"\nVisibility: {weather['visibility']} km"
                
                return response_text
            
            else:
                # Multiple cities
                response_lines = ["Weather for multiple cities:"]
                for city in cities:
                    weather = results[city]
                    if "error" not in weather:
                        response_lines.append(
                            f"\n{weather['city']}, {weather['country']}: "
                            f"{weather['temperature']}°C, {weather['description']}"
                        )
                    else:
                        response_lines.append(
                            f"\n{city}: {weather['error']}"
                        )
                
                return "\n".join(response_lines)
                
        except Exception as e:
            logger.error(f"Error in weather query: {e}")
            return f"An error occurred while fetching weather data: {str(e)}"
    
    def process_query(self, query: str) -> str:
        """
        Main method to process a user query.
        
        Args:
            query: User's input
            
        Returns:
            Assistant's response
        """
        try:
            # Add user message to memory
            self.memory_manager.add_message("user", query)
            
            # Classify intent
            intent = self.classify_intent(query)
            
            # Check if memory compression is needed
            if self.memory_manager.should_summarize():
                logger.info("Compressing conversation history...")
                self.memory_manager.compress_history()
            
            # Handle based on intent
            if intent == "rag":
                response = self.handle_rag_query(query)
            elif intent == "weather_api":
                response = self.handle_weather_query(query)
            else:
                # General conversation
                general_prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("user", "{query}")
                ])
                chain = general_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"query": query})
            
            # Add assistant response to memory
            self.memory_manager.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error: {str(e)}"

