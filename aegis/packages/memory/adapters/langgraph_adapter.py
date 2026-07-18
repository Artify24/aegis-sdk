import logging
from typing import Any, List, Dict, Optional
from packages.memory.provider import BaseMemoryProvider
from langgraph.checkpoint.memory import MemorySaver

# We wrap LangGraph's checkpointer and store so that the SDK never exposes them directly.
# For this adapter, we will implement the BaseMemoryProvider interface using an in-memory
# approach that mirrors how LangGraph handles state natively, acting as a bridge if needed.

logger = logging.getLogger(__name__)

class LangGraphMemoryAdapter(MemorySaver):
    """
    Adapts LangGraph's Memory mechanics into the Aegis BaseMemoryProvider interface.
    Because it subclasses MemorySaver, it acts as a native LangGraph checkpointer 
    (automatically saving conversational state) while ALSO exposing our unified 
    enterprise APIs (read, write, search).
    """
    def __init__(self):
        super().__init__()
        # We maintain a separate store for explicit semantic/knowledge storage 
        # since LangGraph's checkpointer is specifically for graph state/messages.
        self._store: Dict[str, Dict[str, tuple[Any, dict]]] = {}

    async def write(self, namespace: str, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        if namespace not in self._store:
            self._store[namespace] = {}
        self._store[namespace][key] = (value, metadata or {})
        logger.debug(f"LangGraphAdapter wrote to {namespace}:{key}")

    async def read(self, namespace: str, key: str) -> Any | None:
        ns = self._store.get(namespace, {})
        if key in ns:
            return ns[key][0]
        return None

    async def search(self, namespace: str, query: str, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        ns = self._store.get(namespace, {})
        results = []
        query_words = query.lower().split()
        for val, meta in ns.values():
            val_str = str(val).lower()
            if all(word in val_str for word in query_words):
                if metadata_filter:
                    if not all(meta.get(k) == v for k, v in metadata_filter.items()):
                        continue
                results.append(val)
        return results[:top_k]

    async def delete(self, namespace: str, key: str) -> bool:
        ns = self._store.get(namespace, {})
        if key in ns:
            del ns[key]
            logger.debug(f"LangGraphAdapter deleted {namespace}:{key}")
            return True
        return False

    async def clear(self, namespace: str) -> None:
        if namespace in self._store:
            self._store[namespace] = {}
            logger.debug(f"LangGraphAdapter cleared namespace {namespace}")

    async def exists(self, namespace: str, key: str) -> bool:
        return namespace in self._store and key in self._store[namespace]
