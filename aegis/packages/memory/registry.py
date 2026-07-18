from typing import Dict, Optional
import logging
from packages.models import MemorySource
from packages.memory.provider import BaseMemoryProvider

logger = logging.getLogger(__name__)

class MemoryRegistry:
    """
    Source of truth for all configured memory sources and their providers.
    Ensures that Aegis routes memory operations securely without exposing the underlying implementation.
    """
    def __init__(self) -> None:
        self._sources: Dict[str, MemorySource] = {}
        self._providers: Dict[str, BaseMemoryProvider] = {}
        
    def register_provider(self, name: str, provider: BaseMemoryProvider) -> None:
        """Registers a BaseMemoryProvider implementation under a given name."""
        if not isinstance(provider, BaseMemoryProvider):
            raise TypeError(f"Provider '{name}' must implement BaseMemoryProvider.")
        self._providers[name] = provider
        logger.info(f"Registered memory provider: {name}")

    def register_source(self, source: MemorySource) -> None:
        """Registers a MemorySource definition."""
        self._sources[source.name] = source
        logger.info(f"Registered memory source: {source.name} (Provider: {source.provider_name})")

    def get_source(self, name: str) -> MemorySource:
        """Retrieves a MemorySource by name."""
        if name not in self._sources:
            raise KeyError(f"Memory source '{name}' not found in registry.")
        return self._sources[name]

    def get_provider(self, name: str) -> BaseMemoryProvider:
        """Retrieves a provider by name."""
        if name not in self._providers:
            raise KeyError(f"Memory provider '{name}' not found in registry.")
        return self._providers[name]
        
    def get_provider_for_source(self, source_name: str) -> BaseMemoryProvider:
        """Helper to get the configured provider for a specific memory source."""
        source = self.get_source(source_name)
        return self.get_provider(source.provider_name)
