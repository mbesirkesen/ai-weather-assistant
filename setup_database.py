"""Setup script to initialize vector database with OpenWeatherMap documentation."""
import logging
from config import Config
from vector_store import VectorStoreManager
from data_loader import load_documentation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup():
    """Main setup function."""
    logger.info("Starting database setup...")
    
    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Initialize vector store
    try:
        logger.info("Initializing vector store...")
        vector_store = VectorStoreManager()
        
        # Create index (informational)
        vector_store.create_index()
        
        # Load documentation
        logger.info("Loading OpenWeatherMap documentation...")
        docs = load_documentation()
        
        if not docs:
            logger.error("No documentation loaded")
            return
        
        # Add to vector store
        logger.info("Adding documents to vector store...")
        num_chunks = vector_store.add_documents(docs)
        logger.info(f"Added {num_chunks} document chunks to vector store")
        
        logger.info("Setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during setup: {e}")
        raise


if __name__ == "__main__":
    setup()

