"""Test script for the weather assistant."""
import logging
from config import Config
from agent import WeatherAssistant

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_assistant():
    """Test the weather assistant with various queries."""
    logger.info("Initializing weather assistant...")
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Initialize assistant
    assistant = WeatherAssistant()
    
    # Test queries
    test_cases = [
        # RAG queries
        {
            "query": "How do I get an API key for OpenWeatherMap?",
            "type": "RAG"
        },
        {
            "query": "Which endpoint gives current weather data?",
            "type": "RAG"
        },
        # Weather API queries
        {
            "query": "What is the weather in Istanbul right now?",
            "type": "Weather API"
        },
        {
            "query": "Give me the temperature in Paris and London",
            "type": "Weather API"
        }
    ]
    
    print("\n" + "="*80)
    print("TESTING AI WEATHER ASSISTANT")
    print("="*80 + "\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test_case['type']} Query")
        print(f"{'='*80}")
        print(f"Query: {test_case['query']}")
        print("\nResponse:")
        print("-"*80)
        
        try:
            response = assistant.process_query(test_case['query'])
            print(response)
        except Exception as e:
            logger.error(f"Error in test {i}: {e}")
            print(f"Error: {str(e)}")
        
        print("-"*80)
    
    print("\n" + "="*80)
    print("TESTING COMPLETED")
    print("="*80 + "\n")
    
    # Test memory
    print("\nTesting Memory:")
    print(f"Total messages in memory: {len(assistant.memory_manager.conversation_history)}")
    assistant.memory_manager.save_to_disk("test_memory.json")
    print("Memory saved to test_memory.json")


if __name__ == "__main__":
    test_assistant()

