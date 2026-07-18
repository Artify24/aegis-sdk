from typing import Protocol, runtime_checkable
from packages.context import ExecutionContext

@runtime_checkable
class Layer1Stage(Protocol):
    """
    Protocol for a single stage in the Layer 1 pre-execution governance pipeline.
    
    Each stage receives the shared ExecutionContext, performs its analysis or
    enrichment, and updates the context for the next stage in the pipeline.
    """
    async def process(self, context: ExecutionContext) -> None:
        """
        Process the execution context.
        
        Args:
            context: The ExecutionContext to analyze and enrich.
        """
        ...
