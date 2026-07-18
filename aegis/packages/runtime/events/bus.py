import asyncio
import logging
from typing import Callable, Dict, List, Type, Any, Awaitable
from packages.runtime.events.models import RuntimeEvent

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[RuntimeEvent], Awaitable[None]]

class RuntimeEventBus:
    """
    Internal Event Bus for the Runtime Control Plane (Layer 3).
    Decouples execution events from monitoring, tracking, and telemetry.
    """
    def __init__(self):
        self._subscribers: Dict[Type[RuntimeEvent], List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []
        
    def subscribe(self, event_type: Type[RuntimeEvent], handler: EventHandler) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        
    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events (useful for BehaviorMonitor and Tracker)."""
        self._global_subscribers.append(handler)
        
    def unsubscribe(self, event_type: Type[RuntimeEvent], handler: EventHandler) -> None:
        """Unsubscribe a specific handler from a specific event type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            
    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from global events."""
        if handler in self._global_subscribers:
            self._global_subscribers.remove(handler)
        
    async def publish(self, event: RuntimeEvent) -> None:
        """Publish an event to all interested subscribers asynchronously."""
        handlers = self._global_subscribers.copy()
        
        event_type = type(event)
        if event_type in self._subscribers:
            handlers.extend(self._subscribers[event_type])
            
        if not handlers:
            return
            
        # Fire and forget (gather asynchronously to prevent blocking the runtime)
        tasks = [asyncio.create_task(self._safe_invoke(handler, event)) for handler in handlers]
        
        # We await them here for determinism in the current execution step,
        # but in a highly distributed system, this could be pushed to a background worker.
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_invoke(self, handler: EventHandler, event: RuntimeEvent) -> None:
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Event handler {handler.__name__} failed processing {type(event).__name__}: {e}", exc_info=True)
