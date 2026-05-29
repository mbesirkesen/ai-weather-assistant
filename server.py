"""LangGraph server for LangGraph Studio."""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from graph import create_weather_assistant_graph
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Weather Assistant LangGraph Server")

_graph = None


def get_graph():
    """Lazy-load graph after config validation."""
    global _graph
    if _graph is None:
        Config.validate()
        _graph = create_weather_assistant_graph()
    return _graph


@app.on_event("startup")
def startup_validation():
    """Validate configuration on startup with a clear error message."""
    try:
        Config.validate()
        logger.info("Configuration validated — server ready")
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        logger.error("Copy .env.example to .env and fill in your API keys")


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str
    thread_id: Optional[str] = "default"


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    response: str
    intent: Optional[str] = None
    context: Optional[dict] = None


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "AI Weather Assistant LangGraph Server",
        "version": "2.0.0",
        "description": "Advanced LangGraph with conditional routing and multi-step workflow",
        "endpoints": {
            "/graph": "Graph schema",
            "/health": "Health check",
            "/query": "Process a query through the graph (POST)"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        Config.validate()
        return {"status": "healthy", "config": "ok"}
    except ValueError as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)},
        )


@app.get("/graph")
def get_graph_schema():
    """Get the graph schema for LangGraph Studio."""
    try:
        schema = get_graph().to_json()
        return schema
    except Exception as e:
        logger.error(f"Error getting graph schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query through the LangGraph workflow.
    
    This endpoint demonstrates the advanced LangGraph features:
    - Conditional routing based on intent
    - Multi-step state management
    - Agentic workflow
    """
    try:
        # Prepare initial state
        config = {"configurable": {"thread_id": request.thread_id}}
        
        initial_state = {
            "messages": [request.query],
            "query": request.query,
            "intent": None,
            "retrieved_docs": None,
            "weather_data": None,
            "response": None,
            "next_action": "",
            "context": {},
            "error": None
        }
        
        # Invoke the graph
        logger.info(f"Processing query: {request.query}")
        result = get_graph().invoke(initial_state, config)
        
        # Extract response and context
        response_text = result.get("response", "")
        if not response_text and result.get("messages"):
            # Fallback: get last message if response not set
            response_text = result["messages"][-1] if len(result["messages"]) > 1 else ""
        
        return QueryResponse(
            response=response_text,
            intent=result.get("intent"),
            context=result.get("context", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting LangGraph server on port {Config.LANGGRAPH_PORT}")
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=Config.LANGGRAPH_PORT,
        reload=True
    )

