"""Main LangGraph agent file - coordinates RAG, Weather API, and Memory management."""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
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
            # Find top 3 relevant documents using MongoDB Atlas vector search
            docs = self.vector_store.similarity_search(query, k=3)
            
            if not docs:
                return "I couldn't find relevant documentation. Please try rephrasing your question."
            
            # Combine found documents
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # RAG prompt: System info + Context + Question
            rag_prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt + "\n\nUse the following documentation to answer the question:"),
                ("system", "Documentation:\n{context}"),
                ("user", "{question}")
            ])
            
            # LangChain chain: prompt -> LLM -> string
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
        
        Steps:
        1. Extract city names from query using LLM
        2. Call OpenWeatherMap API for each city
        3. Present data in user-friendly format
        
        Why LLM extraction? Regex is brittle and doesn't work well with natural language.
        """
        try:
            # Extract city names using LLM
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract city names from the user's weather query. Return ONLY the city names, separated by commas."),
                ("user", "{query}")
            ])
            
            extraction_chain = extraction_prompt | self.llm | StrOutputParser()
            cities_str = extraction_chain.invoke({"query": query})
            
            # Convert comma-separated string to list
            cities = [city.strip() for city in cities_str.split(",") if city.strip()]
            
            if not cities:
                return "I couldn't identify which cities you're asking about. Please specify the city name(s)."
            
            # Fetch weather for each city
            results = {}
            for city in cities:
                weather = self.weather_api.get_current_weather(city)
                results[city] = weather
            
            # Format output: detailed for single city, compact for multiple cities
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
                # Compact format for multiple cities
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
                # General conversation - respond with LLM only
                general_prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("user", "{query}")
                ])
                chain = general_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"query": query})
            
            # 5. Add response to memory
            self.memory_manager.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error: {str(e)}"

