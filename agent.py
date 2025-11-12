"""Main LangGraph agent file - coordinates RAG, Weather API, and Memory management."""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any, Iterable
import logging

from config import Config
from weather_api import WeatherAPI
from vector_store import VectorStoreManager
from memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class WeatherAssistant:
    """
    Main AI assistant class.
    
    This class coordinates three main components:
    1. RAG: Answers documentation questions
    2. Weather API: Fetches live weather data
    3. Memory: Manages conversation history
    """
    
    def __init__(self):
        """Initialize the assistant's core components."""
        # LLM: For intent classification and text generation
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,  # gpt-4o-mini: fast and cheap
            temperature=0.7,  # Creativity level (0-1)
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Other components
        self.weather_api = WeatherAPI()  # Live weather data
        self.vector_store = VectorStoreManager()  # RAG vector search
        self.memory_manager = MemoryManager()  # Conversation history
        
        # System prompt: Defines LLM identity and capabilities
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
        Detect the intent of the user's query.
        
        We use LLM instead of rule-based because:
        - Better understanding of natural language
        - No need to write rules for each query type
        - Automatically adapts to new question patterns
        
        Returns:
            "rag": Documentation questions
            "weather_api": Live weather requests
            "general": General conversation
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
            # Send prompt to LLM and get intent
            response = self.llm.invoke(prompt.format_messages(query=query))
            intent = response.content.strip().lower()
            logger.info(f"Intent classified as: {intent}")
            return intent
        except Exception as e:
            # Return "general" on error to prevent system crash
            logger.error(f"Error classifying intent: {e}")
            return "general"
    
    def retrieve_relevant_documents(self, query: str, k: int = 3):
        """
        Retrieve documents relevant to a RAG query using the vector store.
        
        Args:
            query: User query string
            k: Number of documents to retrieve
        
        Returns:
            List of Documents (can be empty on failure)
        """
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            logger.info("Retrieved %d documents for query", len(docs))
            return docs
        except Exception as e:
            logger.error(f"Error retrieving documents for RAG: {e}")
            return []
    
    def generate_rag_response(self, query: str, docs: Iterable) -> str:
        """
        Generate a RAG response from retrieved documents.
        
        Args:
            query: Original user query
            docs: Iterable of documents
        
        Returns:
            Generated response string
        """
        docs = list(docs) if docs else []
        if not docs:
            return "I couldn't find relevant documentation. Please try rephrasing your question."
        
        context = "\n\n".join(getattr(doc, "page_content", str(doc)) for doc in docs)
        
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
    
    def handle_rag_query(self, query: str) -> str:
        """
        Handle RAG (Retrieval-Augmented Generation) queries.
        
        RAG approach provides these advantages:
        - Putting all documentation in prompt uses too many tokens
        - Vector search finds only relevant parts
        - Cost and speed optimization
        
        Steps:
        1. Find relevant documents using vector search
        2. Send as context to LLM
        3. LLM generates answer from context + question
        """
        try:
            # Find relevant documents using MongoDB Atlas vector search
            docs = self.retrieve_relevant_documents(query, k=3)
            return self.generate_rag_response(query, docs)
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return f"An error occurred while searching documentation: {str(e)}"
    
    def extract_cities(self, query: str) -> List[str]:
        """
        Extract city names from a weather-related query using the LLM.
        
        Args:
            query: User query
        
        Returns:
            List of city names
        """
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract city names from the user's weather query. Return ONLY the city names, separated by commas."),
            ("user", "{query}")
        ])
        
        extraction_chain = extraction_prompt | self.llm | StrOutputParser()
        cities_str = extraction_chain.invoke({"query": query})
        cities = [city.strip() for city in cities_str.split(",") if city.strip()]
        return cities
    
    def get_weather_for_cities(self, cities: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch weather data for a list of cities.
        
        Args:
            cities: Iterable of city names
        
        Returns:
            Mapping of city name to weather data or error payload
        """
        results: Dict[str, Dict[str, Any]] = {}
        for city in cities:
            try:
                results[city] = self.weather_api.get_current_weather(city)
            except Exception as e:
                logger.error(f"Error fetching weather for {city}: {e}")
                results[city] = {"error": str(e)}
        return results
    
    def format_weather_response(self, cities: List[str], results: Dict[str, Dict[str, Any]]) -> str:
        """
        Format weather data into a user-friendly response.
        
        Args:
            cities: List of requested cities (preserves ordering)
            results: Weather data mapping
        
        Returns:
            Formatted response string
        """
        if not cities:
            return "I couldn't identify which cities you're asking about. Please specify the city name(s)."
        
        if len(cities) == 1:
            city = cities[0]
            weather = results.get(city, {"error": "No data returned."})
            
            if "error" in weather:
                return f"Sorry, I couldn't get weather data: {weather['error']}"
            
            response_text = f"""Current weather in {weather['city']}, {weather['country']}:

Temperature: {weather['temperature']}°C (feels like {weather['feels_like']}°C)
Condition: {weather['description']}
Humidity: {weather['humidity']}%
Wind: {weather['wind_speed']} m/s {weather.get('wind_direction_desc', '')}
Cloud coverage: {weather['clouds']}%
Pressure: {weather['pressure']} hPa"""
            
            if weather.get('visibility'):
                response_text += f"\nVisibility: {weather['visibility']} km"
            
            return response_text
        
        response_lines = ["Weather for multiple cities:"]
        for city in cities:
            weather = results.get(city, {"error": "No data returned."})
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
    
    def handle_weather_query(self, query: str) -> str:
        """
        Handle live weather queries.
        
        Steps:
        1. Extract city names from query using LLM
        2. Call OpenWeatherMap API for each city
        3. Present data in user-friendly format
        
        Why LLM extraction? Regex is brittle and doesn't work well with natural language.
        """
        try:
            cities = self.extract_cities(query)

            if not cities:
                return "I couldn't identify which cities you're asking about. Please specify the city name(s)."
            
            results = self.get_weather_for_cities(cities)
            return self.format_weather_response(cities, results)
                
        except Exception as e:
            logger.error(f"Error in weather query: {e}")
            return f"An error occurred while fetching weather data: {str(e)}"
    
    def generate_general_response(self, query: str) -> str:
        """
        Generate a general conversation response with the LLM.
        
        Args:
            query: User query
        
        Returns:
            Model-generated response
        """
        general_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{query}")
        ])
        chain = general_prompt | self.llm | StrOutputParser()
        return chain.invoke({"query": query})
    
    def process_query(self, query: str) -> str:
        """
        Main query processing method - all queries pass through here.
        
        Workflow:
        1. Add user message to memory
        2. Detect intent (RAG/Weather/General)
        3. Compress if context is full
        4. Call appropriate handler based on intent
        5. Add response to memory and return
        """
        try:
            # 1. Add to memory
            self.memory_manager.add_message("user", query)
            
            # 2. Intent classification
            intent = self.classify_intent(query)
            
            # 3. Compress if context is full (user won't notice)
            if self.memory_manager.should_summarize():
                logger.info("Compressing conversation history...")
                self.memory_manager.compress_history()
            
            # 4. Intent-based routing
            if intent == "rag":
                response = self.handle_rag_query(query)
            elif intent == "weather_api":
                response = self.handle_weather_query(query)
            else:
                response = self.generate_general_response(query)
            
            # 5. Add response to memory
            self.memory_manager.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error: {str(e)}"

