"""LangGraph server for LangGraph Studio."""
import logging
from fastapi import FastAPI
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, List, Literal
import operator

from graph import create_weather_assistant_graph
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Create the graph
graph = create_weather_assistant_graph()


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "AI Weather Assistant LangGraph Server",
        "version": "1.0.0",
        "endpoints": {
            "/graph": "Graph schema",
            "/health": "Health check"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/graph")
def get_graph_schema():
    """Get the graph schema for LangGraph Studio."""
    schema = graph.to_json()
    return schema


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting LangGraph server on port {Config.LANGGRAPH_PORT}")
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=Config.LANGGRAPH_PORT,
        reload=True
    )

