"""LangGraph graph definition for the weather assistant."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict, Any
import operator

from agent import WeatherAssistant
import logging

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
    """State for the LangGraph."""
    messages: Annotated[List[Dict[str, str]], operator.add]
    route_trace: Annotated[List[str], operator.add]
    user_query: str
    intent: str
    retrieval_context: List[str]
    cities: List[str]
    weather_results: Dict[str, Dict[str, Any]]
    response: str
    next_action: str
    context: Dict[str, Any]


def create_weather_assistant_graph():
    """
    Create the LangGraph for the weather assistant.
    
    Returns:
        Compiled LangGraph
    """
    assistant = WeatherAssistant()

    def _append_route(state: GraphState, node_name: str) -> None:
        """Track traversal path for debugging and observability."""
        routes = state.get("route_trace", [])
        routes.append(node_name)
        state["route_trace"] = routes

    def _ensure_context(state: GraphState) -> Dict[str, Any]:
        """Return a mutable context dictionary on the state."""
        context = state.get("context") or {}
        state["context"] = context
        return context

    def ingest_user_message(state: GraphState) -> GraphState:
        """Normalize and record the incoming user message."""
        _append_route(state, "ingest_user_message")
        messages = state.get("messages") or []

        if not messages:
            logger.warning("No incoming message found; using empty string.")
            query = ""
            normalized_messages: List[Dict[str, str]] = [{"role": "user", "content": ""}]
        else:
            last_message = messages[-1]
            if isinstance(last_message, dict):
                query = last_message.get("content", "")
                normalized_messages = messages  # type: ignore[assignment]
            else:
                query = str(last_message)
                normalized_messages = [
                    *messages[:-1],  # type: ignore[arg-type]
                    {"role": "user", "content": query}
                ]

        state["messages"] = normalized_messages  # type: ignore[assignment]
        state["user_query"] = query
        assistant.memory_manager.add_message("user", query)

        context = _ensure_context(state)
        context["memory_messages_before"] = len(assistant.memory_manager.conversation_history)
        logger.info("Ingested user message: %s", query)
        return state

    def prepare_memory(state: GraphState) -> GraphState:
        """Summarize memory if needed before routing."""
        _append_route(state, "prepare_memory")
        try:
            if assistant.memory_manager.should_summarize():
                logger.info("Summarizing conversation history before proceeding.")
                assistant.memory_manager.compress_history()
                state["context"]["memory_summarized"] = True
            else:
                state["context"]["memory_summarized"] = False
        except Exception as e:
            logger.error("Error while preparing memory: %s", e)
            state["context"]["memory_error"] = str(e)
        return state

    def classify_intent(state: GraphState) -> GraphState:
        """Classify user intent using the assistant."""
        _append_route(state, "classify_intent")
        query = state.get("user_query", "")
        intent = assistant.classify_intent(query)
        state["intent"] = intent
        state["context"]["intent"] = intent
        logger.info("Intent classified as %s", intent)
        return state

    def route_from_intent(state: GraphState) -> str:
        """Route based on detected intent."""
        intent = state.get("intent")
        if intent in {"rag", "weather_api", "general"}:
            return intent  # type: ignore[return-value]
        logger.warning("Unknown intent '%s'; routing to fallback.", intent)
        return "fallback"

    def retrieve_context(state: GraphState) -> GraphState:
        """Retrieve documents for RAG."""
        _append_route(state, "retrieve_context")
        query = state.get("user_query", "")
        docs = assistant.retrieve_relevant_documents(query, k=3)
        state["retrieval_context"] = [
            getattr(doc, "page_content", str(doc)) for doc in docs
        ]
        state["context"]["retrieved_documents"] = len(state["retrieval_context"])
        state["context"]["rag_sources"] = state["retrieval_context"]
        return state

    def generate_rag_response(state: GraphState) -> GraphState:
        """Generate RAG answer using retrieved documents."""
        _append_route(state, "generate_rag_response")
        query = state.get("user_query", "")
        docs = state.get("retrieval_context", [])
        response = assistant.generate_rag_response(query, docs)
        state["response"] = response
        state["context"]["selected_route"] = "rag"
        return state

    def extract_cities(state: GraphState) -> GraphState:
        """Extract city names for weather queries."""
        _append_route(state, "extract_cities")
        query = state.get("user_query", "")
        cities = assistant.extract_cities(query)
        state["cities"] = cities
        state["context"]["city_count"] = len(cities)
        if not cities:
            state["response"] = "I couldn't identify which cities you're asking about. Please specify the city name(s)."
            state["context"]["selected_route"] = "weather_api"
        return state

    def fetch_weather_data(state: GraphState) -> GraphState:
        """Fetch weather data for extracted cities."""
        _append_route(state, "fetch_weather_data")
        cities = state.get("cities") or []
        if not cities:
            return state
        results = assistant.get_weather_for_cities(cities)
        state["weather_results"] = results
        state["context"]["weather_results_ready"] = True
        return state

    def compose_weather_response(state: GraphState) -> GraphState:
        """Compose response from weather data."""
        _append_route(state, "compose_weather_response")
        cities = state.get("cities") or []
        results = state.get("weather_results") or {}
        response = assistant.format_weather_response(cities, results)
        state["response"] = response
        state["context"]["selected_route"] = "weather_api"
        state["context"]["weather_results"] = results
        return state

    def generate_general_response(state: GraphState) -> GraphState:
        """Generate general conversation response."""
        _append_route(state, "generate_general_response")
        query = state.get("user_query", "")
        response = assistant.generate_general_response(query)
        state["response"] = response
        state["context"]["selected_route"] = "general"
        return state

    def update_memory(state: GraphState) -> GraphState:
        """Persist assistant response to memory."""
        _append_route(state, "update_memory")
        response = state.get("response", "")
        assistant.memory_manager.add_message("assistant", response)
        state["context"]["memory_messages_after"] = len(assistant.memory_manager.conversation_history)
        return state

    def finalize_response(state: GraphState) -> GraphState:
        """Finalize the response for LangGraph output."""
        _append_route(state, "finalize_response")
        response = state.get("response", "")
        messages = state.get("messages") or []
        messages.append({"role": "assistant", "content": response})
        state["messages"] = messages
        state["next_action"] = "complete"
        return state

    def handle_failure(state: GraphState) -> GraphState:
        """Fallback handler when routing fails."""
        _append_route(state, "handle_failure")
        error_message = state.get("response") or "I couldn't determine how to help with that request."
        state["response"] = error_message
        state["context"]["selected_route"] = "fallback"
        return state

    workflow = StateGraph(GraphState)

    workflow.add_node("ingest_user_message", ingest_user_message)
    workflow.add_node("prepare_memory", prepare_memory)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_rag_response", generate_rag_response)
    workflow.add_node("extract_cities", extract_cities)
    workflow.add_node("fetch_weather_data", fetch_weather_data)
    workflow.add_node("compose_weather_response", compose_weather_response)
    workflow.add_node("generate_general_response", generate_general_response)
    workflow.add_node("update_memory", update_memory)
    workflow.add_node("finalize_response", finalize_response)
    workflow.add_node("handle_failure", handle_failure)

    workflow.set_entry_point("ingest_user_message")
    workflow.add_edge("ingest_user_message", "prepare_memory")
    workflow.add_edge("prepare_memory", "classify_intent")
    workflow.add_conditional_edges(
        "classify_intent",
        route_from_intent,
        {
            "rag": "retrieve_context",
            "weather_api": "extract_cities",
            "general": "generate_general_response",
            "fallback": "handle_failure",
        },
    )
    workflow.add_edge("retrieve_context", "generate_rag_response")
    workflow.add_edge("generate_rag_response", "update_memory")
    workflow.add_edge("extract_cities", "fetch_weather_data")
    workflow.add_edge("fetch_weather_data", "compose_weather_response")
    workflow.add_edge("compose_weather_response", "update_memory")
    workflow.add_edge("generate_general_response", "update_memory")
    workflow.add_edge("handle_failure", "update_memory")
    workflow.add_edge("update_memory", "finalize_response")
    workflow.add_edge("finalize_response", END)

    app = workflow.compile()

    logger.info("LangGraph created successfully with conditional routing and multi-step workflow.")
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

