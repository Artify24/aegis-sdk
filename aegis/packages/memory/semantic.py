from typing import List, Dict, Any, Optional
import logging
from packages.memory.manager import MemoryManager

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    High-level API for Semantic (Vector) Memory operations.
    Delegates all algorithm specifics (like embeddings, cosine similarity) to the 
    underlying memory provider via the Layer 4 Memory Manager.
    """
    def __init__(self, memory_manager: MemoryManager, default_source: str = "semantic_knowledge"):
        self.manager = memory_manager
        self.default_source = default_source

    async def add_knowledge(self, key: str, text: str, metadata: Optional[Dict[str, Any]] = None, source_name: Optional[str] = None) -> None:
        """Stores a piece of knowledge into the semantic namespace."""
        source = source_name or self.default_source
        await self.manager.write(source, key, text, metadata)
        logger.debug(f"Added knowledge to semantic source '{source}' under key '{key}'")

    async def search_similar(self, query: str, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None, source_name: Optional[str] = None) -> List[Any]:
        """
        Retrieves the top_k most similar entries to the query.
        The underlying provider handles the vectorization and similarity matching.
        """
        source = source_name or self.default_source
        results = await self.manager.search(source, query, top_k, metadata_filter)
        return results
        
    async def delete_knowledge(self, key: str, source_name: Optional[str] = None) -> bool:
        """Removes a specific knowledge chunk."""
        source = source_name or self.default_source
        return await self.manager.delete(source, key)
