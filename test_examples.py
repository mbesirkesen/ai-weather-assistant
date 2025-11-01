"""Test examples for the weather assistant."""
from agent import WeatherAssistant
from config import Config

# Initialize the assistant
assistant = WeatherAssistant()

print("=" * 80)
print("AI WEATHER ASSISTANT - TEST EXAMPLES")
print("=" * 80)
print()

# Example 1: RAG Query (Documentation)
print("Example 1: RAG Query - API Documentation")
print("-" * 80)
query1 = "How do I get an API key for OpenWeatherMap?"
print(f"Query: {query1}")
print()
response1 = assistant.process_query(query1)
print(f"Response: {response1}")
print()

# Example 2: Weather Query - Single City
print("Example 2: Weather Query - Single City")
print("-" * 80)
query2 = "What is the weather in Istanbul right now?"
print(f"Query: {query2}")
print()
response2 = assistant.process_query(query2)
print(f"Response: {response2}")
print()

# Example 3: Weather Query - Multiple Cities
print("Example 3: Weather Query - Multiple Cities")
print("-" * 80)
query3 = "Give me the temperature in Paris and London"
print(f"Query: {query3}")
print()
response3 = assistant.process_query(query3)
print(f"Response: {response3}")
print()

# Example 4: General Conversation
print("Example 4: General Conversation")
print("-" * 80)
query4 = "What can you do?"
print(f"Query: {query4}")
print()
response4 = assistant.process_query(query4)
print(f"Response: {response4}")
print()

print("=" * 80)
print("TESTING COMPLETED")
print("=" * 80)

