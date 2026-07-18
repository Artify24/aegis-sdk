import logging
import time
import asyncio
from typing import Any
from packages.models import ExecutionMetadata
from packages.runtime.managers.registry import ToolRegistry, RegisteredTool

logger = logging.getLogger(__name__)

class ToolExecutorError(Exception):
    """Raised for errors during tool execution validation or resolution."""
    pass

class ToolExecutor:
    """
    Executes ApprovedActions by resolving tools through the ToolRegistry.
    Collects execution metrics and captures exceptions.
    Does NOT handle retries or timeouts (delegated to their respective managers).
    """
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        
    async def execute(self, action: Any) -> tuple[Any, ExecutionMetadata]:
        """
        Takes an ApprovedAction (or ProposedAction), resolves the tool, invokes it,
        and returns the raw result alongside ExecutionMetadata.
        """
        tool_name = getattr(action, "tool_name", "")
        arguments = getattr(action, "arguments", {})
        
        logger.debug(f"Executing tool {tool_name}")
        
        start_time = time.time()
        success = False
        raw_result = None
        exception_details = None
        
        try:
            # 1. Resolve Tool
            registered_tool = self.registry.get_tool(tool_name)
            
            # 2. Validate Metadata
            if not registered_tool.metadata.enabled:
                raise ToolExecutorError(f"Tool '{tool_name}' is disabled and cannot be executed.")
                
            # 3. Invoke Tool
            executable = registered_tool.executable
            
            # Support LangChain BaseTool interface (ainvoke/invoke) and raw callables
            if hasattr(executable, "ainvoke"):
                raw_result = await executable.ainvoke(arguments)
            elif hasattr(executable, "invoke"):
                raw_result = await asyncio.to_thread(executable.invoke, arguments)
            elif asyncio.iscoroutinefunction(executable):
                raw_result = await executable(**arguments)
            elif callable(executable):
                raw_result = await asyncio.to_thread(executable, **arguments)
            else:
                raise ToolExecutorError(f"Tool '{tool_name}' is not callable.")
                
            success = True
        except Exception as e:
            logger.error(f"Execution failed for {tool_name}: {e}")
            raw_result = str(e)
            exception_details = str(e)
            
        execution_time_ms = (time.time() - start_time) * 1000
        
        # 4. Collect Execution Metrics
        metadata = ExecutionMetadata(
            tool_name=tool_name,
            success=success,
            execution_time_ms=execution_time_ms,
            retries_attempted=0, # RetryManager handles this later
            timeout_occurred=False, # TimeoutManager handles this later
            exception_details=exception_details
        )
        
        # 5. Return ExecutionResult (raw_result + metadata)
        return raw_result, metadata
