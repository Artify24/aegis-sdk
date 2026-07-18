import logging
from typing import Dict, List, Any
from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.events.models import RuntimeEvent, ToolStarted, ToolFinished

logger = logging.getLogger(__name__)

class BehaviorMonitor:
    """
    Observes live execution to track API calls, Tool Calls, Memory I/O, etc.
    Builds a complete execution graph similar to LangSmith.
    """
    def __init__(self, event_bus: RuntimeEventBus):
        self.event_bus = event_bus
        self.execution_graph: List[Dict[str, Any]] = []
        
        self.event_bus.subscribe_all(self._observe_event)
        
    async def _observe_event(self, event: RuntimeEvent) -> None:
        """Record the event into the execution graph."""
        node = {
            "event_type": type(event).__name__,
            "timestamp": event.timestamp,
            "step_id": event.step_id,
            "details": event.__dict__.copy()
        }
        self.execution_graph.append(node)
        
        if isinstance(event, ToolStarted):
            logger.info(f"[BehaviorMonitor] Observed Tool Start: {event.tool_name}")
        elif isinstance(event, ToolFinished):
            logger.info(f"[BehaviorMonitor] Observed Tool Finish: {event.tool_name} (Success: {event.success})")
            
    def get_graph(self) -> List[Dict[str, Any]]:
        """Returns the full execution graph for this session."""
        return self.execution_graph
