"""Test with your own queries."""
from agent import WeatherAssistant

# Initialize the assistant
assistant = WeatherAssistant()

print("=" * 80)
print("AI WEATHER ASSISTANT - CUSTOM TEST")
print("=" * 80)
print()

# ADD YOUR CUSTOM QUERIES HERE
# Replace the examples below with your own questions:

queries = [
    "What is the weather in Tokyo?",
    "How do I use the OpenWeatherMap API?",
    "What's the temperature in New York and Los Angeles?",
]

for i, query in enumerate(queries, 1):
    print(f"\nQuery {i}: {query}")
    print("-" * 80)
    response = assistant.process_query(query)
    print(response)
    print()

print("=" * 80)
print("Test completed!")
print("=" * 80)

