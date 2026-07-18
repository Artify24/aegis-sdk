import logging
from typing import Any, AsyncGenerator, Tuple
from packages.models import ExecutionMetadata

logger = logging.getLogger(__name__)

class StreamingManager:
    """
    Manages streaming responses from providers.
    Provides a proxy generator that yields chunks to the SDK/Developer without 
    requiring architectural changes to the Executors.
    """
    
    async def stream(self, execution_coroutine) -> AsyncGenerator[Any, None]:
        """
        Takes a coroutine that returns (raw_result, ExecutionMetadata).
        If raw_result is an async or sync generator, it proxies the chunks sequentially.
        If it's a static result, it yields it as a single chunk.
        """
        logger.debug("Streaming manager initializing...")
        
        try:
            # Await the executor to get the (result, metadata) tuple
            # If the provider is streaming, `raw_result` will be the generator object itself.
            raw_result, metadata = await execution_coroutine
            
            if not metadata.success:
                logger.error(f"Execution failed before streaming: {metadata.exception_details}")
                yield f"Error: {metadata.exception_details}"
                return

            # Proxy async generator
            if hasattr(raw_result, '__aiter__'):
                async for chunk in raw_result:
                    yield chunk
                    
            # Proxy sync generator (excluding strings/dicts/lists which have __iter__ but aren't streams)
            elif hasattr(raw_result, '__iter__') and not isinstance(raw_result, (str, bytes, dict, list)):
                for chunk in raw_result:
                    yield chunk
                    
            # Fallback for static results (not actually a stream)
            else:
                yield raw_result
                
        except Exception as e:
            logger.error(f"Streaming failed during chunk iteration: {e}")
            yield f"StreamingError: {str(e)}"
