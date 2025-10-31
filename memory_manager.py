"""Memory management for conversation context and long-term memory."""
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
from config import Config
import logging
import json

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages short-term and long-term memory for the AI assistant."""
    
    def __init__(self):
        """Initialize the memory manager."""
        self.conversation_history: List[Dict[str, str]] = []
        self.summarizer = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.3,
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.max_context_length = Config.MAX_CONTEXT_LENGTH
    
    def add_message(self, role: str, content: str):
        """
        Add a message to conversation history.
        
        Args:
            role: Message role (user/assistant)
            content: Message content
        """
        self.conversation_history.append({"role": role, "content": content})
        logger.debug(f"Added message to history (total: {len(self.conversation_history)})")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.
        
        Returns:
            List of message dictionaries
        """
        return self.conversation_history.copy()
    
    def get_conversation_context(self) -> str:
        """
        Get formatted conversation context for prompts.
        
        Returns:
            Formatted conversation history as string
        """
        context_lines = []
        for msg in self.conversation_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def should_summarize(self) -> bool:
        """
        Check if conversation should be summarized to save context.
        
        Returns:
            True if summarization needed
        """
        # Check if approaching context limit
        context_length = len(self.get_conversation_context())
        threshold = self.max_context_length * Config.CONVERSATION_SUMMARY_THRESHOLD
        
        return context_length > threshold
    
    def summarize_conversation(self) -> str:
        """
        Create a summary of the conversation to compress history.
        
        Returns:
            Summary of the conversation
        """
        try:
            if not self.conversation_history:
                return "No conversation history yet."
            
            conversation_text = self.get_conversation_context()
            
            prompt = f"""Summarize this conversation between a user and an AI weather assistant.
Focus on:
- User's main questions and requests
- Important context or preferences
- Any specific cities or weather topics mentioned
- Key information that should be remembered

Conversation:
{conversation_text}

Provide a concise summary:"""
            
            response = self.summarizer.invoke(prompt)
            summary = response.content
            
            logger.info("Conversation summarized")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Error creating summary."
    
    def compress_history(self):
        """Compress conversation history by summarizing older messages."""
        try:
            summary = self.summarize_conversation()
            
            # Keep only the most recent messages
            recent_count = max(2, len(self.conversation_history) // 4)
            recent_messages = self.conversation_history[-recent_count:]
            
            # Reset history with summary
            self.conversation_history = [
                {"role": "assistant", "content": f"[Previous conversation summary: {summary}]"}
            ]
            self.conversation_history.extend(recent_messages)
            
            logger.info("Conversation history compressed")
            
        except Exception as e:
            logger.error(f"Error compressing history: {e}")
    
    def clear_history(self):
        """Clear all conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_recent_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """
        Get the most recent n messages.
        
        Args:
            n: Number of recent messages to return
            
        Returns:
            List of recent messages
        """
        return self.conversation_history[-n:] if len(self.conversation_history) > n else self.conversation_history
    
    def save_to_disk(self, filepath: str = "memory.json"):
        """Save conversation history to disk (long-term memory)."""
        try:
            data = {
                "conversation_history": self.conversation_history,
                "metadata": {
                    "total_messages": len(self.conversation_history),
                    "summary": self.summarize_conversation() if self.conversation_history else None
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved memory to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def load_from_disk(self, filepath: str = "memory.json"):
        """Load conversation history from disk (long-term memory)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.conversation_history = data.get("conversation_history", [])
            logger.info(f"Loaded memory from {filepath} ({len(self.conversation_history)} messages)")
            
        except FileNotFoundError:
            logger.info(f"Memory file {filepath} not found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")

