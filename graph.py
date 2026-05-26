"""LangGraph graph definition for the weather assistant with advanced workflow."""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List, Literal, Optional, Dict, Any
import operator

from agent import WeatherAssistant
from config import Config
import logging

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """Enhanced state for the LangGraph with multi-step workflow support."""
    messages: Annotated[List[str], operator.add]
    query: str
    intent: Optional[str]
    retrieved_docs: Optional[List[Dict[str, Any]]]
    weather_data: Optional[Dict[str, Any]]
    response: Optional[str]
    next_action: str
    context: Optional[Dict[str, Any]]
    error: Optional[str]


def create_weather_assistant_graph():
    """
    Create an advanced LangGraph for the weather assistant with:
    - Conditional routing based on intent
    - Multi-step state management
    - Agentic workflow with separate nodes for each step
    
    Workflow:
    1. classify_intent -> Detects query intent
    2. route -> Conditional routing based on intent
    3. retrieve_docs (if RAG) -> Vector search for documentation
    4. fetch_weather (if weather_api) -> Live weather data
    5. handle_general (if general) -> General conversation
    6. generate_response -> Final response generation
    7. update_memory -> Update conversation history
    
    Returns:
        Compiled LangGraph with checkpointing
    """
    # Initialize the assistant components
    assistant = WeatherAssistant()
    
    def classify_intent(state: GraphState) -> GraphState:
        """
        Node 1: Classify user intent using LLM.
        
        This is the first step in our agentic workflow.
        """
        try:
            query = state.get("query", "")
            if not query and state.get("messages"):
                query = state["messages"][-1]
                state["query"] = query
            
            logger.info(f"Classifying intent for query: {query}")
            
            # Use assistant's intent classification
            intent = assistant.classify_intent(query)
            
            state["intent"] = intent
            state["next_action"] = intent
            context = state.get("context") or {}
            context["intent_classification"] = intent
            state["context"] = context
            
            logger.info(f"Intent classified as: {intent}")
            return state
            
        except Exception as e:
            logger.error(f"Error in classify_intent: {e}")
            state["error"] = str(e)
            state["intent"] = "general"
            state["next_action"] = "general"
            return state
    
    def retrieve_docs(state: GraphState) -> GraphState:
        """
        Node 2: Retrieve relevant documentation using RAG.
        
        This node is called when intent is "rag".
        """
        try:
            query = state.get("query", "")
            logger.info(f"Retrieving docs for RAG query: {query}")
            
            # Perform vector search
            docs = assistant.vector_store.similarity_search(query, k=3)
            
            # Convert to serializable format
            retrieved_docs = []
            for doc in docs:
                retrieved_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            state["retrieved_docs"] = retrieved_docs
            state["next_action"] = "generate_response"
            context = state.get("context") or {}
            context["docs_retrieved"] = len(retrieved_docs)
            state["context"] = context
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents")
            return state
            
        except Exception as e:
            logger.error(f"Error in retrieve_docs: {e}")
            state["error"] = str(e)
            state["retrieved_docs"] = []
            state["next_action"] = "generate_response"
            return state
    
    def fetch_weather(state: GraphState) -> GraphState:
        """
        Node 3: Fetch live weather data from API.
        
        This node is called when intent is "weather_api".
        """
        try:
            query = state.get("query", "")
            logger.info(f"Fetching weather data for query: {query}")
            
            # Extract city names using LLM
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract city names from the user's weather query. Return ONLY the city names, separated by commas."),
                ("user", "{query}")
            ])
            
            extraction_chain = extraction_prompt | assistant.llm | StrOutputParser()
            cities_str = extraction_chain.invoke({"query": query})
            cities = [city.strip() for city in cities_str.split(",") if city.strip()]
            
            if not cities:
                state["weather_data"] = {"error": "No cities identified"}
                state["next_action"] = "generate_response"
                return state
            
            # Fetch weather for each city
            weather_results = {}
            for city in cities:
                weather = assistant.weather_api.get_current_weather(city)
                weather_results[city] = weather
            
            state["weather_data"] = weather_results
            state["next_action"] = "generate_response"
            context = state.get("context") or {}
            context["cities_queried"] = cities
            context["weather_fetched"] = len(weather_results)
            state["context"] = context
            
            logger.info(f"Fetched weather for {len(cities)} cities")
            return state
            
        except Exception as e:
            logger.error(f"Error in fetch_weather: {e}")
            state["error"] = str(e)
            state["weather_data"] = {"error": str(e)}
            state["next_action"] = "generate_response"
            return state
    
    def handle_general(state: GraphState) -> GraphState:
        """
        Node 4: Handle general conversation queries.
        
        This node is called when intent is "general".
        """
        try:
            query = state.get("query", "")
            logger.info(f"Handling general conversation query: {query}")
            
            # General queries don't need special data retrieval
            # Just mark that we're ready for response generation
            state["next_action"] = "generate_response"
            context = state.get("context") or {}
            context["conversation_type"] = "general"
            state["context"] = context
            
            return state
            
        except Exception as e:
            logger.error(f"Error in handle_general: {e}")
            state["error"] = str(e)
            state["next_action"] = "generate_response"
            return state
    
    def generate_response(state: GraphState) -> GraphState:
        """
        Node 5: Generate final response based on intent and retrieved data.
        
        This node synthesizes all information to create the final answer.
        """
        try:
            query = state.get("query", "")
            intent = state.get("intent", "general")
            
            logger.info(f"Generating response for intent: {intent}")
            
            # Check if memory should be compressed
            if assistant.memory_manager.should_summarize():
                logger.info("Compressing conversation history...")
                assistant.memory_manager.compress_history()
            
            # Add user message to memory
            assistant.memory_manager.add_message("user", query)
            
            # Generate response based on intent and available data
            if intent == "rag":
                # Use RAG handler with retrieved docs
                retrieved_docs = state.get("retrieved_docs", [])
                if not retrieved_docs:
                    response = "I couldn't find relevant documentation. Please try rephrasing your question."
                else:
                    context = "\n\n".join([doc["content"] for doc in retrieved_docs])
                    response = assistant.handle_rag_query(query)
                    
            elif intent == "weather_api":
                # Use weather handler with fetched data
                weather_data = state.get("weather_data", {})
                if not weather_data or "error" in str(weather_data):
                    response = assistant.handle_weather_query(query)
                else:
                    # Format weather response
                    cities = list(weather_data.keys())
                    if len(cities) == 1:
                        weather = weather_data[cities[0]]
                        if "error" in weather:
                            response = f"Sorry, I couldn't get weather data: {weather['error']}"
                        else:
                            response = f"""Current weather in {weather['city']}, {weather['country']}:

Temperature: {weather['temperature']}°C (feels like {weather['feels_like']}°C)
Condition: {weather['description']}
Humidity: {weather['humidity']}%
Wind: {weather['wind_speed']} m/s {weather.get('wind_direction_desc', '')}
Cloud coverage: {weather['clouds']}%
Pressure: {weather['pressure']} hPa"""
                            if weather.get('visibility'):
                                response += f"\nVisibility: {weather['visibility']} km"
                    else:
                        response_lines = ["Weather for multiple cities:"]
                        for city in cities:
                            weather = weather_data[city]
                            if "error" not in weather:
                                response_lines.append(
                                    f"\n{weather['city']}, {weather['country']}: "
                                    f"{weather['temperature']}°C, {weather['description']}"
                                )
                            else:
                                response_lines.append(f"\n{city}: {weather['error']}")
                        response = "\n".join(response_lines)
                        
            else:
                # General conversation
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                general_prompt = ChatPromptTemplate.from_messages([
                    ("system", assistant.system_prompt),
                    ("user", "{query}")
                ])
                chain = general_prompt | assistant.llm | StrOutputParser()
                response = chain.invoke({"query": query})
            
            state["response"] = response
            state["messages"].append(response)
            state["next_action"] = "update_memory"
            context = state.get("context") or {}
            context["response_generated"] = True
            state["context"] = context
            
            logger.info("Response generated successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
            error_response = f"An error occurred while generating response: {str(e)}"
            state["error"] = str(e)
            state["response"] = error_response
            state["messages"].append(error_response)
            state["next_action"] = "update_memory"
            return state
    
    def update_memory(state: GraphState) -> GraphState:
        """
        Node 6: Update conversation memory with the response.
        
        This is the final step before ending the workflow.
        """
        try:
            response = state.get("response", "")
            if response:
                assistant.memory_manager.add_message("assistant", response)
                
            state["next_action"] = "complete"
            context = state.get("context") or {}
            context["memory_updated"] = True
            context["memory_messages"] = len(assistant.memory_manager.conversation_history)
            state["context"] = context
            
            logger.info("Memory updated successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in update_memory: {e}")
            state["error"] = str(e)
            state["next_action"] = "complete"
            return state
    
    def route(state: GraphState) -> Literal["retrieve_docs", "fetch_weather", "handle_general"]:
        """
        Conditional routing function based on intent.
        
        This implements conditional routing - one of LangGraph's key features.
        """
        intent = state.get("intent", "general")
        logger.info(f"Routing based on intent: {intent}")
        
        if intent == "rag":
            return "retrieve_docs"
        elif intent == "weather_api":
            return "fetch_weather"
        else:
            return "handle_general"
    
    # Create the graph with enhanced workflow
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("retrieve_docs", retrieve_docs)
    workflow.add_node("fetch_weather", fetch_weather)
    workflow.add_node("handle_general", handle_general)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("update_memory", update_memory)
    
    # Set entry point
    workflow.set_entry_point("classify_intent")
    
    # Add conditional routing from classify_intent
    workflow.add_conditional_edges(
        "classify_intent",
        route,
        {
            "retrieve_docs": "retrieve_docs",
            "fetch_weather": "fetch_weather",
            "handle_general": "handle_general"
        }
    )
    
    # Add edges from intent-specific nodes to response generation
    workflow.add_edge("retrieve_docs", "generate_response")
    workflow.add_edge("fetch_weather", "generate_response")
    workflow.add_edge("handle_general", "generate_response")
    
    # Add edge from response generation to memory update
    workflow.add_edge("generate_response", "update_memory")
    
    # Add edge from memory update to END
    workflow.add_edge("update_memory", END)
    
    # Compile the graph with checkpointing for state persistence
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    logger.info("Advanced LangGraph created successfully with conditional routing and multi-step workflow")
    return app


# Don't create graph instance at module level to avoid initialization issues
# graph = create_weather_assistant_graph()


def get_graph():
    """Get the compiled LangGraph for LangGraph Studio."""
    return create_weather_assistant_graph()


# LangGraph Studio compatible configuration
def get_config():
    """Get configuration for LangGraph Studio."""
    return {
        "configurable": {
            "thread_id": "1",
        }
    }

