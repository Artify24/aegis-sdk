from typing import Protocol, Any, runtime_checkable, List, Dict, Optional

@runtime_checkable
class BaseMemoryProvider(Protocol):
    """
    The foundational interface for all Aegis memory providers.
    Whether backed by LangGraph, Redis, Pinecone, Chroma, or Postgres,
    the provider must strictly conform to these methods to ensure
    Layer 4 remains completely vendor-agnostic.
    """
    
    async def write(self, namespace: str, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Writes a value to the specified namespace.
        """
        ...
        
    async def read(self, namespace: str, key: str) -> Any | None:
        """
        Reads a value from the specified namespace by key.
        Returns None if the key does not exist.
        """
        ...
        
    async def search(self, namespace: str, query: str, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Performs a semantic or keyword search within the namespace.
        The underlying algorithm (vector vs. text search) is determined by the provider.
        """
        ...
        
    async def delete(self, namespace: str, key: str) -> bool:
        """
        Deletes a specific key from the namespace.
        Returns True if the key was deleted, False if it did not exist.
        """
        ...
        
    async def clear(self, namespace: str) -> None:
        """
        Clears all data within the specified namespace.
        """
        ...
        
    async def exists(self, namespace: str, key: str) -> bool:
        """
        Checks if a key exists in the namespace.
        """
        ...
