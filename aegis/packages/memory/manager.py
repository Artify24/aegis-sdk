from typing import Any, List, Dict, Optional
import logging
import time
import uuid
from packages.models import MemoryMetadata
from packages.memory.registry import MemoryRegistry
from packages.memory.policies import MemoryPolicyEvaluator, MemoryPolicyException

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Orchestrates all memory operations in Layer 4.
    Resolves the provider via the MemoryRegistry, enforces policies, and delegates 
    execution to the underlying provider (LangGraph, Redis, Pinecone, etc.).
    """
    def __init__(self, registry: MemoryRegistry):
        self.registry = registry

    async def write(self, source_name: str, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        source = self.registry.get_source(source_name)
        if not source.enabled:
            logger.warning(f"Memory source '{source_name}' is disabled. Write operation aborted.")
            return

        provider = self.registry.get_provider(source.provider_name)
        
        # Phase 4.8 - Apply Memory Policies
        MemoryPolicyEvaluator.evaluate_write(source, key, value, context=metadata)
        
        # Phase 4.9 - Capture Telemetry
        start_time = time.time()
        status = "success"
        try:
            await provider.write(source.namespace, key, value, metadata)
        except Exception:
            status = "failed"
            raise
        finally:
            self._log_telemetry(source, "write", start_time, status)

    async def read(self, source_name: str, key: str) -> Any | None:
        source = self.registry.get_source(source_name)
        if not source.enabled:
            return None
            
        # Phase 4.8 - Apply Memory Policies (using empty context for now, ideally passed from higher level)
        MemoryPolicyEvaluator.evaluate_read(source, key, context={})
        
        provider = self.registry.get_provider(source.provider_name)
        
        start_time = time.time()
        status = "success"
        try:
            return await provider.read(source.namespace, key)
        except Exception:
            status = "failed"
            raise
        finally:
            self._log_telemetry(source, "read", start_time, status)

    async def search(self, source_name: str, query: str, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        source = self.registry.get_source(source_name)
        if not source.enabled:
            return []
            
        if not source.semantic:
            logger.warning(f"Memory source '{source_name}' is not marked as semantic. "
                           f"Search relies entirely on the provider's fallback mechanism.")
            
        provider = self.registry.get_provider(source.provider_name)
        
        start_time = time.time()
        status = "success"
        try:
            return await provider.search(source.namespace, query, top_k, metadata_filter)
        except Exception:
            status = "failed"
            raise
        finally:
            self._log_telemetry(source, "search", start_time, status)

    async def delete(self, source_name: str, key: str) -> bool:
        source = self.registry.get_source(source_name)
        if not source.enabled:
            return False
            
        provider = self.registry.get_provider(source.provider_name)
        
        start_time = time.time()
        status = "success"
        try:
            return await provider.delete(source.namespace, key)
        except Exception:
            status = "failed"
            raise
        finally:
            self._log_telemetry(source, "delete", start_time, status)

    async def clear(self, source_name: str) -> None:
        source = self.registry.get_source(source_name)
        if not source.enabled:
            return
            
        provider = self.registry.get_provider(source.provider_name)
        await provider.clear(source.namespace)

    async def exists(self, source_name: str, key: str) -> bool:
        source = self.registry.get_source(source_name)
        if not source.enabled:
            return False
            
        provider = self.registry.get_provider(source.provider_name)
        return await provider.exists(source.namespace, key)
        
    def _log_telemetry(self, source, operation: str, start_time: float, status: str) -> None:
        latency_ms = (time.time() - start_time) * 1000
        telemetry = MemoryMetadata(
            memory_id=str(uuid.uuid4()),
            provider_name=source.provider_name,
            namespace=source.namespace,
            operation=operation,
            latency_ms=latency_ms,
            status=status,
            timestamp=start_time
        )
        logger.debug(f"Memory Telemetry [{status.upper()}]: {operation} in {source.namespace} took {latency_ms:.2f}ms")
        # In the future, Layer 5 will subscribe to these telemetry events.
