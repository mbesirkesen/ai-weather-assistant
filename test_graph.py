"""Test script for the LangGraph workflow."""
import logging
from config import Config
from graph import create_weather_assistant_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_graph():
    """Test the LangGraph with various queries."""
    logger.info("Initializing LangGraph...")
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Create the graph
    graph = create_weather_assistant_graph()
    
    # Test queries
    test_cases = [
        {
            "query": "How do I get an API key for OpenWeatherMap?",
            "type": "RAG",
            "expected_intent": "rag"
        },
        {
            "query": "Which endpoint gives current weather data?",
            "type": "RAG",
            "expected_intent": "rag"
        },
        {
            "query": "What is the weather in Istanbul right now?",
            "type": "Weather API",
            "expected_intent": "weather_api"
        },
        {
            "query": "Give me the temperature in Paris and London",
            "type": "Weather API",
            "expected_intent": "weather_api"
        },
        {
            "query": "Hello, what can you help me with?",
            "type": "General",
            "expected_intent": "general"
        }
    ]
    
    print("\n" + "="*80)
    print("TESTING LANGGRAPH WORKFLOW")
    print("="*80 + "\n")
    
    config = {"configurable": {"thread_id": "test_thread"}}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test_case['type']} Query")
        print(f"{'='*80}")
        print(f"Query: {test_case['query']}")
        print(f"Expected Intent: {test_case['expected_intent']}")
        print("\nResponse:")
        print("-"*80)
        
        try:
            # Prepare initial state
            initial_state = {
                "messages": [test_case['query']],
                "query": test_case['query'],
                "intent": None,
                "retrieved_docs": None,
                "weather_data": None,
                "response": None,
                "next_action": "",
                "context": {},
                "error": None
            }
            
            # Invoke the graph
            result = graph.invoke(initial_state, config)
            
            # Display results
            print(result.get("response", "No response generated"))
            print("\n" + "-"*80)
            print("Graph State:")
            print(f"  Intent: {result.get('intent')}")
            print(f"  Next Action: {result.get('next_action')}")
            print(f"  Context: {result.get('context')}")
            
            if result.get("retrieved_docs"):
                print(f"  Retrieved Docs: {len(result['retrieved_docs'])} documents")
            
            if result.get("weather_data"):
                print(f"  Weather Data: {len(result['weather_data'])} cities")
            
            if result.get("error"):
                print(f"  Error: {result['error']}")
            
            # Verify intent
            actual_intent = result.get("intent")
            if actual_intent == test_case['expected_intent']:
                print(f"\n✓ Intent classification correct: {actual_intent}")
            else:
                print(f"\n✗ Intent mismatch. Expected: {test_case['expected_intent']}, Got: {actual_intent}")
                
        except Exception as e:
            logger.error(f"Error in test {i}: {e}")
            print(f"Error: {str(e)}")
        
        print("-"*80)
    
    print("\n" + "="*80)
    print("TESTING COMPLETED")
    print("="*80 + "\n")
    
    print("\nLangGraph Features Demonstrated:")
    print("  ✓ Conditional Routing: Intent-based node selection")
    print("  ✓ Multi-step State Management: State passed through multiple nodes")
    print("  ✓ Agentic Workflow: Separate nodes for each processing step")
    print("  ✓ Checkpointing: State persistence with MemorySaver")


if __name__ == "__main__":
    test_graph()

