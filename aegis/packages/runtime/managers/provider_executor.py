import logging
import time
import asyncio
from typing import Any
from packages.models import ExecutionMetadata
from packages.runtime.managers.provider_registry import ProviderRegistry

logger = logging.getLogger(__name__)

class ProviderExecutorError(Exception):
    """Raised for errors during provider execution validation or resolution."""
    pass

class ProviderExecutor:
    """
    Executes provider tasks (e.g. ChatCompletion, Embeddings) by resolving the provider
    through the ProviderRegistry. Collects execution metrics and captures exceptions.
    Does NOT handle retries or timeouts (delegated to their respective managers).
    """
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    async def execute(self, task_type: str, provider_name: str | None = None, **kwargs) -> tuple[Any, ExecutionMetadata]:
        """
        Executes a task on the specified provider (or default if None).
        Args:
            task_type: The type of task (e.g., 'generate', 'embed').
            provider_name: Optional provider name to use instead of default.
            kwargs: Arguments passed to the provider method.
        """
        logger.debug(f"Executing provider task '{task_type}'")

        start_time = time.time()
        success = False
        raw_result = None
        exception_details = None
        actual_provider_name = provider_name or "unknown"

        try:
            # 1. Resolve Provider
            registered_provider = self.registry.get_provider(provider_name)
            actual_provider_name = registered_provider.metadata.name

            # 2. Validate Metadata
            if not registered_provider.metadata.enabled:
                raise ProviderExecutorError(f"Provider '{actual_provider_name}' is disabled.")
            
            if registered_provider.metadata.capabilities and task_type not in registered_provider.metadata.capabilities:
                raise ProviderExecutorError(f"Provider '{actual_provider_name}' does not support capability '{task_type}'.")

            # 3. Invoke Provider Method
            executable = registered_provider.executable
            method = getattr(executable, task_type, None)
            
            if not method:
                raise ProviderExecutorError(f"Provider '{actual_provider_name}' does not implement method '{task_type}'.")

            if asyncio.iscoroutinefunction(method):
                raw_result = await method(**kwargs)
            elif callable(method):
                raw_result = await asyncio.to_thread(method, **kwargs)
            else:
                raise ProviderExecutorError(f"'{task_type}' on Provider '{actual_provider_name}' is not callable.")

            success = True
        except Exception as e:
            logger.error(f"Provider execution failed for {task_type}: {e}")
            raw_result = str(e)
            exception_details = str(e)

        execution_time_ms = (time.time() - start_time) * 1000

        # 4. Collect Execution Metrics
        metadata = ExecutionMetadata(
            tool_name=f"provider_{actual_provider_name}_{task_type}",
            success=success,
            execution_time_ms=execution_time_ms,
            retries_attempted=0, # RetryManager handles this later
            timeout_occurred=False, # TimeoutManager handles this later
            exception_details=exception_details
        )

        return raw_result, metadata
