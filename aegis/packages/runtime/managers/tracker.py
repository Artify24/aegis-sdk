import uuid
import logging
from typing import Optional
from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.events.models import RuntimeEvent

logger = logging.getLogger(__name__)

class ExecutionTracker:
    """
    Maintains execution context (trace_id, execution_id) and enriches all runtime events.
    Subscribes to all events on the RuntimeEventBus.
    """
    def __init__(self, event_bus: RuntimeEventBus, agent_id: str):
        self.event_bus = event_bus
        self.agent_id = agent_id
        
        # State
        self.trace_id = str(uuid.uuid4())
        self.execution_id = str(uuid.uuid4())
        self.request_id: Optional[str] = None
        self.current_step_id: Optional[str] = None
        self.parent_step_id: Optional[str] = None
        
        # Subscribe to all events to enrich them
        self.event_bus.subscribe_all(self._enrich_and_track_event)
        
    async def _enrich_and_track_event(self, event: RuntimeEvent) -> None:
        """Enrich the event with tracking IDs before it gets processed by others."""
        if not event.trace_id:
            event.trace_id = self.trace_id
        if not event.execution_id:
            event.execution_id = self.execution_id
        if not event.agent_id:
            event.agent_id = self.agent_id
            
        if self.request_id and not event.request_id:
            event.request_id = self.request_id
            
        if self.current_step_id and not event.step_id:
            event.step_id = self.current_step_id
            
        if self.parent_step_id and not event.parent_step:
            event.parent_step = self.parent_step_id
            
        logger.debug(f"[Tracker] Tracked {type(event).__name__} for trace {self.trace_id}")

    def cleanup(self) -> None:
        """Unsubscribe from the event bus to prevent memory leaks."""
        self.event_bus.unsubscribe_all(self._enrich_and_track_event)
