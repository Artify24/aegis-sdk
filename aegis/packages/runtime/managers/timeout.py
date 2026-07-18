import logging
import asyncio
from typing import Callable, Any, Tuple
from packages.models import ExecutionMetadata

logger = logging.getLogger(__name__)

class TimeoutManager:
    """
    Enforces strict timeouts on tool, provider, or workflow executions.
    Ensures that no execution can hang indefinitely.
    """
    
    async def execute_with_timeout(
        self, 
        coroutine_func: Callable[..., Any], 
        timeout_seconds: float, 
        fallback_name: str = "unknown_task",
        **kwargs
    ) -> Tuple[Any, ExecutionMetadata]:
        """
        Wraps a coroutine_func that returns (result, ExecutionMetadata) in an asyncio.wait_for.
        If a timeout occurs, returns a synthesized failed ExecutionMetadata instead of crashing.
        """
        try:
            logger.debug(f"Executing {fallback_name} with timeout: {timeout_seconds}s")
            return await asyncio.wait_for(coroutine_func(**kwargs), timeout=timeout_seconds)
            
        except asyncio.TimeoutError:
            logger.error(f"Execution timed out for {fallback_name} after {timeout_seconds}s")
            
            # Construct a graceful failure metadata indicating a timeout
            metadata = ExecutionMetadata(
                tool_name=fallback_name,
                success=False,
                execution_time_ms=timeout_seconds * 1000,
                retries_attempted=0, # We don't know retry count from here, but the execution failed
                timeout_occurred=True,
                exception_details=f"Execution exceeded the strict timeout limit of {timeout_seconds} seconds."
            )
            
            return f"TimeoutError: Execution exceeded {timeout_seconds} seconds.", metadata
