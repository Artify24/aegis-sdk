import logging
import asyncio
import random
from typing import Callable, Any, Tuple
from packages.models import ExecutionMetadata

logger = logging.getLogger(__name__)

class RetryManager:
    """
    Wraps execution managers (ToolExecutor, ProviderExecutor) with policy-driven retry logic.
    Supports: none, fixed, linear, exponential (with jitter).
    """
    
    async def execute_with_retry(self, func: Callable[..., Any], retry_policy: str = "none", max_retries: int = 3, base_delay: float = 1.0, **kwargs) -> Tuple[Any, ExecutionMetadata]:
        """
        Executes a callable (usually from an Executor) that returns a tuple of (result, ExecutionMetadata).
        Retries based on the metadata.success flag.
        """
        attempt = 0
        
        while True:
            # Execute the function which should return (raw_result, ExecutionMetadata)
            result, metadata = await func(**kwargs)
            metadata.retries_attempted = attempt
            
            # Stop if successful, out of retries, or policy is none
            if metadata.success or attempt >= max_retries or retry_policy == "none":
                return result, metadata
                
            # Calculate delay based on policy
            if retry_policy == "fixed":
                delay = base_delay
            elif retry_policy == "linear":
                delay = base_delay * (attempt + 1)
            elif retry_policy == "exponential":
                delay = base_delay * (2 ** attempt)
            else:
                delay = base_delay # default fallback
                
            # Add small jitter (e.g., +/- 20%) to prevent thundering herd
            jitter = delay * 0.2 * random.uniform(-1, 1)
            final_delay = max(0, delay + jitter)
            
            logger.warning(f"Execution failed for {metadata.tool_name}. Retrying attempt {attempt+1}/{max_retries} in {final_delay:.2f}s...")
            await asyncio.sleep(final_delay)
            attempt += 1
