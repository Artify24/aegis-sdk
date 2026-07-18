from typing import List, Dict, Any
import logging
from packages.memory.manager import MemoryManager

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    High-level API for managing conversation histories, context reconstruction, 
    and session isolation. Operates strictly via the Layer 4 Memory Manager.
    """
    def __init__(self, memory_manager: MemoryManager, source_name: str = "conversation_history"):
        self.manager = memory_manager
        self.source_name = source_name

    async def add_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Appends a message to the session's conversation history."""
        history = await self.manager.read(self.source_name, session_id) or []
        history.append(message)
        await self.manager.write(self.source_name, session_id, history)
        logger.debug(f"Added message to conversation session '{session_id}'")

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves the full conversation history for an isolated session."""
        history = await self.manager.read(self.source_name, session_id)
        return history or []

    async def clear_session(self, session_id: str) -> None:
        """Clears all conversation history for a specific session."""
        await self.manager.delete(self.source_name, session_id)
        logger.info(f"Cleared conversation session '{session_id}'")
        
    async def get_recent_messages(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves the last 'limit' messages for context reconstruction."""
        history = await self.get_history(session_id)
        return history[-limit:] if history else []
