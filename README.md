# AI Weather Assistant

A Python-based AI assistant powered by LangGraph, LangChain, and OpenAI API. This assistant combines Retrieval-Augmented Generation (RAG) with live API integration to answer questions about weather API documentation and provide real-time weather data.

## Project Overview

The AI Weather Assistant is a sophisticated conversational AI that demonstrates:

1. **Retrieval-Augmented Generation (RAG)**: Answers questions based on OpenWeatherMap API documentation
2. **Agentic Behavior**: Fetches live weather data from OpenWeatherMap API
3. **Memory Management**: Implements both short-term (conversation context) and long-term (persistent) memory
4. **LangGraph Integration**: Built with LangGraph for orchestration and LangSmith for tracing

### Key Capabilities

- 📚 **Documentation Q&A**: Answers questions about API keys, endpoints, parameters, and usage
- 🌤️ **Live Weather Data**: Fetches current weather conditions for any city worldwide
- 🧠 **Context Awareness**: Remembers conversation history and context
- 🔄 **Smart Memory**: Automatically compresses long conversations to manage context limits
- 📊 **Tracing**: Full LangSmith integration for debugging and monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Intent Classification                         │
│                   (LLM-based routing)                            │
└─────────────────────────────────────────────────────────────────┘
            ↓                              ↓
┌─────────────────────┐         ┌────────────────────────┐
│   RAG Path          │         │   Weather API Path     │
│─────────────────────│         │────────────────────────│
│ 1. Query Vector     │         │ 1. Extract City Names  │
│    Database         │         │ 2. Call OpenWeatherMap │
│ 2. Retrieve Docs    │         │ 3. Format Response     │
│ 3. Generate Answer  │         │                        │
└─────────────────────┘         └────────────────────────┘
            ↓                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Memory Manager                                │
│  • Short-term: Conversation History                              │
│  • Long-term: Persistent Storage                                 │
│  • Compression: Summarize when needed                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Final Response                             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction

1. **Agent Orchestrator**: Routes queries to appropriate handlers based on intent
2. **Vector Store**: MongoDB Atlas with embeddings for RAG
3. **Weather API**: Direct integration with OpenWeatherMap API
4. **Memory Manager**: Handles conversation context and persistence
5. **LangGraph**: State management and workflow orchestration
6. **LangSmith**: Tracing and monitoring

## Technology Stack

- **Language**: Python 3.9+
- **LLM Provider**: OpenAI (GPT-4o-mini, text-embedding-3-small)
- **Frameworks**: 
  - LangGraph (orchestration)
  - LangChain (chain composition)
  - LangSmith (tracing)
- **Vector Database**: MongoDB Atlas
- **API Integration**: OpenWeatherMap API
- **Server**: FastAPI + Uvicorn
- **Interface**: LangGraph Studio

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- MongoDB Atlas account (free tier available)
- OpenAI API key
- OpenWeatherMap API key
- LangSmith API key

### Installation Steps

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ai-weather-assistant
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
   - Copy `env.example` to `.env`:
```bash
cp env.example .env
```
   - Edit `.env` and fill in all API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=ai-weather-assistant
LANGCHAIN_TRACING_V2=true
MONGODB_ATLAS_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE_NAME=ai_assistant_db
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here
```

5. **Set up MongoDB Atlas**:
   - Create a free cluster at https://www.mongodb.com/atlas
   - Get your connection string
   - Create a vector search index in MongoDB Atlas UI:
     - Go to Atlas Search in your cluster
     - Click "Create Search Index" → "JSON Editor"
     - Paste this configuration:
     ```json
     {
       "mappings": {
         "dynamic": true,
         "fields": {
           "embedding": {
             "type": "knnVector",
             "dimensions": 1536,
             "similarity": "cosine"
           }
         }
       }
     }
     ```
     - Index name: `vector_index`
     - Collection: `weather_docs`

6. **Populate the vector database**:
```bash
python setup_database.py
```

This will:
- Download/load OpenWeatherMap documentation
- Create embeddings
- Store in MongoDB Atlas

## How to Run Locally

### Option 1: Run LangGraph Server (for LangGraph Studio)

1. **Start the LangGraph server**:
```bash
python server.py
```

The server will start on `http://127.0.0.1:20240`

2. **Connect with LangGraph Studio**:
   - Install LangGraph Studio CLI (if not already installed):
```bash
npm install -g @langchain/langgraph-studio
```
   - Open LangGraph Studio and connect to the local server

### Option 2: Run Direct Testing

Test the assistant directly with:
```bash
python test_assistant.py
```

This runs predefined test queries and displays responses.

### Option 3: Interactive Testing

For interactive testing in Python:
```python
from agent import WeatherAssistant
from config import Config

# Validate config
Config.validate()

# Initialize assistant
assistant = WeatherAssistant()

# Ask questions
response = assistant.process_query("What is the weather in Istanbul?")
print(response)

response = assistant.process_query("How do I get an API key?")
print(response)
```

## Example Interactions

### RAG Queries (Documentation)

**Query 1**: "How do I get an API key?"

**Response**: 
```
To get an API key for OpenWeatherMap:
1. Sign up at openweathermap.org
2. Verify your email address
3. Navigate to API keys section in your account
4. Generate a new key or use the default key provided

The API key should be included in all requests as the 'appid' parameter.
Free tier allows 60 calls per minute.
```

**Query 2**: "Which endpoint gives current weather data?"

**Response**:
```
The current weather data endpoint is:
api.openweathermap.org/data/2.5/weather

Main parameters:
- q: City name (e.g., "London,uk" or "Istanbul,tr")
- appid: Your API key (required)
- units: Temperature units (standard, metric, imperial)
- lang: Language for descriptions

Example request:
GET https://api.openweathermap.org/data/2.5/weather?q=London,uk&appid=YOUR_KEY&units=metric
```

### Weather API Queries (Live Data)

**Query 3**: "What is the weather in Istanbul right now?"

**Response**:
```
Current weather in Istanbul, TR:

🌡️  Temperature: 22°C (feels like 20°C)
☁️  Condition: Partly Cloudy
💧 Humidity: 65%
🌬️  Wind: 3.2 m/s NE
☁️  Cloud coverage: 40%
📊 Pressure: 1013 hPa
👁️  Visibility: 10 km
```

**Query 4**: "Give me the temperature in Paris and London"

**Response**:
```
Weather for multiple cities:

Paris, FR: 15°C, Light Rain
London, GB: 18°C, Overcast Clouds
```

## Memory Implementation

### Short-Term Memory (Conversation Context)

- **Storage**: In-memory list of message dictionaries
- **Management**: Automatic compression when approaching context limit
- **Strategy**: Summarize older messages while keeping recent context
- **Threshold**: 80% of max context length triggers compression

**How it works**:
```python
# Messages stored as:
[
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi! How can I help?"},
  ...
]

# When approaching limit:
# 1. Summarize entire conversation
# 2. Keep last 25% of messages
# 3. Prepend summary as context
```

### Long-Term Memory (Persistent Storage)

- **Storage**: JSON files on disk
- **Features**: Save/load conversation history across sessions
- **Metadata**: Includes summaries and statistics

**Usage**:
```python
# Save memory
assistant.memory_manager.save_to_disk("memory.json")

# Load memory
assistant.memory_manager.load_from_disk("memory.json")
```

## LangGraph Studio Compatibility

The assistant is fully compatible with LangGraph Studio:

1. **Graph Definition**: State machine defined in `graph.py`
2. **Server**: FastAPI server exposing graph endpoints
3. **State Management**: TypedDict-based state for type safety
4. **Tracing**: Automatic LangSmith integration

## LangSmith Tracing

All operations are traced through LangSmith:

- Query processing
- API calls
- Vector searches
- Memory operations

To view traces:
1. Ensure `LANGCHAIN_TRACING_V2=true` in `.env`
2. Set `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT`
3. Access traces at https://smith.langchain.com

## Project Structure

```
ai-weather-assistant/
├── agent.py                 # Main assistant logic
├── config.py               # Configuration management
├── data_loader.py          # Documentation loader
├── graph.py                # LangGraph definition
├── memory_manager.py       # Memory management
├── server.py              # LangGraph server
├── setup_database.py      # Database setup script
├── test_assistant.py      # Test script
├── vector_store.py        # Vector store operations
├── weather_api.py         # OpenWeatherMap API client
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
├── .gitignore           # Git ignore rules
└── README.md           # This file
```

## Known Limitations and Future Work

### Current Limitations

1. **Rate Limits**: OpenAI and OpenWeatherMap rate limits apply
2. **Context Window**: Limited by OpenAI's context window
3. **Single Language**: Currently optimized for English
4. **Documentation**: Static fallback if web scraping fails
5. **No Multi-Threading**: Sequential processing only

### Future Improvements

1. **🌍 Multi-Language Support**: Expand to multiple languages
2. **⚡ Async Processing**: Implement async/await for better performance
3. **📊 Advanced Analytics**: Enhanced LangSmith dashboards
4. **🔄 Retry Logic**: Better error handling and retries
5. **💾 Database Memory**: Migrate long-term memory to MongoDB
6. **🎨 UI Enhancement**: Add a web interface
7. **🧩 Tool Expansion**: Add more tools (forecasts, historical data)
8. **🔒 Security**: Enhanced API key management

## Troubleshooting

### MongoDB Connection Issues

If you get connection errors:
```bash
# Check your connection string
# Ensure IP whitelist in MongoDB Atlas allows your IP
# Verify database name and collection name
```

### OpenAI API Errors

```bash
# Verify API key is correct
# Check account has credits
# Confirm rate limits not exceeded
```

### Vector Index Issues

```bash
# Ensure index is created in MongoDB Atlas
# Check index name matches config
# Verify embedding dimensions (1536 for text-embedding-3-small)
```

## Contact

For questions about this assignment:
- Email: meltem@smartup.network
- GitHub: meltemseyhan

## License

This project is created for educational purposes.

---

**Note**: This assistant requires internet connectivity for:
- OpenAI API calls
- OpenWeatherMap API calls
- MongoDB Atlas connection
- LangSmith tracing

Make sure all API keys are valid and services are accessible before running.

