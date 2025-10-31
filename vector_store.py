"""Vector store management for RAG using MongoDB Atlas."""
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymongo import MongoClient
from config import Config
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector store operations for OpenWeatherMap documentation."""
    
    def __init__(self):
        """Initialize the vector store manager."""
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.client = MongoClient(Config.MONGODB_ATLAS_URI)
        self.db = self.client[Config.MONGODB_DATABASE_NAME]
        self.collection = self.db[Config.MONGODB_COLLECTION_NAME]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def add_documents(self, texts):
        """
        Add documents to the vector store.
        
        Args:
            texts: List of text strings to add
        """
        try:
            # Split documents into chunks
            documents = []
            for i, text in enumerate(texts):
                splits = self.text_splitter.split_text(text)
                for j, split in enumerate(splits):
                    # Generate embedding
                    embedding = self.embeddings.embed_query(split)
                    
                    documents.append({
                        "page_content": split,
                        "embedding": embedding,
                        "metadata": {
                            "source": f"doc_{i}",
                            "chunk_index": j
                        }
                    })
            
            # Add to MongoDB
            if documents:
                self.collection.insert_many(documents)
                logger.info(f"Added {len(documents)} document chunks to vector store")
                return len(documents)
            return 0
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def similarity_search(self, query, k=5):
        """
        Search for similar documents using MongoDB Atlas Vector Search.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Use MongoDB Atlas Vector Search
            results = list(
                self.collection.aggregate([
                    {
                        "$vectorSearch": {
                            "index": "vector_index",
                            "path": "embedding",
                            "queryVector": query_embedding,
                            "numCandidates": k * 10,
                            "limit": k
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "page_content": 1,
                            "metadata": 1,
                            "score": {"$meta": "vectorSearchScore"}
                        }
                    }
                ])
            )
            
            # Convert to Document objects for compatibility
            from langchain_core.documents import Document
            documents = []
            for result in results:
                documents.append(
                    Document(
                        page_content=result.get("page_content", ""),
                        metadata=result.get("metadata", {})
                    )
                )
            
            return documents
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            # Fallback to simple text search if vector search fails
            return []
    
    def create_index(self):
        """
        Create vector search index in MongoDB Atlas.
        This should be done once manually in MongoDB Atlas UI or via script.
        """
        # Note: Index creation is typically done in MongoDB Atlas UI
        # The index definition should be:
        index_definition = {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": 1536,  # text-embedding-3-small dimension
                    "similarity": "cosine"
                }
            ]
        }
        logger.info("Vector index definition:")
        logger.info(index_definition)
        logger.info("Please create this index in MongoDB Atlas UI")
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            self.collection.delete_many({})
            logger.info("Cleared vector store collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")

