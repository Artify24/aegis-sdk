from typing import Any, Dict, List
from packages.models import ProviderMetadata, RegisteredProvider

class ProviderRegistryError(Exception):
    """Base exception for ProviderRegistry errors."""
    pass

class ProviderNotFoundError(ProviderRegistryError):
    """Raised when a provider is not found in the registry."""
    pass

class ProviderRegistry:
    """
    The Provider Registry manages multiple AI providers (OpenAI, Groq, Anthropic, etc.).
    It ensures Runtime never depends directly on a concrete provider class.
    """
    def __init__(self):
        self._providers: Dict[str, RegisteredProvider] = {}
        self._default_provider_name: str | None = None

    def register_provider(self, executable: Any, metadata: ProviderMetadata, is_default: bool = False) -> None:
        """
        Registers an executable provider with strongly-typed metadata.
        Optionally sets it as the default provider for the runtime.
        """
        if not metadata.name:
            raise ProviderRegistryError("Provider must have a name.")
            
        self._providers[metadata.name] = RegisteredProvider(
            metadata=metadata,
            executable=executable
        )
        
        if is_default or self._default_provider_name is None:
            self._default_provider_name = metadata.name

    def get_provider(self, name: str | None = None) -> RegisteredProvider:
        """
        Retrieves a registered provider by name. 
        If name is None, returns the default provider.
        Raises ProviderNotFoundError if missing or if no default exists.
        """
        target_name = name or self._default_provider_name
        
        if not target_name:
            raise ProviderNotFoundError("No provider name specified and no default provider exists.")
            
        provider = self._providers.get(target_name)
        if not provider:
            raise ProviderNotFoundError(f"Provider '{target_name}' is not registered.")
            
        return provider

    def get_metadata(self, name: str) -> ProviderMetadata:
        """Retrieves only the metadata for a specific provider."""
        return self.get_provider(name).metadata

    def list_providers(self, include_disabled: bool = False) -> List[RegisteredProvider]:
        """Lists all registered providers."""
        return [
            provider for provider in self._providers.values()
            if include_disabled or provider.metadata.enabled
        ]
        
    def get_enabled_providers(self) -> List[RegisteredProvider]:
        """Returns only enabled providers."""
        return self.list_providers(include_disabled=False)

    def get_default_provider(self) -> RegisteredProvider:
        """Convenience method to strictly get the default provider."""
        return self.get_provider(name=None)
