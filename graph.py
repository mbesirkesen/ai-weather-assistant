"""LangGraph graph definition for the weather assistant."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator

from agent import WeatherAssistant
from config import Config
import logging

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State for the LangGraph."""
    messages: Annotated[List[str], operator.add]
    next_action: str
    context: dict


def create_weather_assistant_graph():
    """
    Create the LangGraph for the weather assistant.
    
    Returns:
        Compiled LangGraph
    """
    # Initialize the assistant
    assistant = WeatherAssistant()
    
    def process_query(state: GraphState) -> GraphState:
        """
        Main processing node that handles all queries.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with response
        """
        try:
            # Get the last message as user input
            if state.get("messages"):
                last_message = state["messages"][-1]
            else:
                last_message = ""
            
            logger.info(f"Processing query: {last_message}")
            
            # Process through the assistant
            response = assistant.process_query(last_message)
            
            # Update state with response
            state["messages"].append(response)
            state["next_action"] = "complete"
            state["context"] = {
                "assistant_response": response,
                "memory_messages": len(assistant.memory_manager.conversation_history)
            }
            
            logger.info("Query processed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            error_response = f"An error occurred: {str(e)}"
            state["messages"].append(error_response)
            state["next_action"] = "complete"
            return state
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("process_query", process_query)
    
    # Add edges
    workflow.set_entry_point("process_query")
    workflow.add_edge("process_query", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("LangGraph created successfully")
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

