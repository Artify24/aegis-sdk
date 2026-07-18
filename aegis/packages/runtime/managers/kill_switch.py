import logging
import asyncio
from typing import List, Callable
from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.events.models import KillSwitchActivated, ExecutionCancelled

logger = logging.getLogger(__name__)

class KillSwitchManager:
    """
    Runtime Controller capable of abruptly halting execution.
    Supports Manual, Dashboard, Emergency, Timeout, Budget, and Policy stops.
    """
    def __init__(self, event_bus: RuntimeEventBus):
        self.event_bus = event_bus
        self._activated = False
        self._cancellation_callbacks: List[Callable[[], None]] = []
        
        self.event_bus.subscribe(KillSwitchActivated, self._on_kill_switch)
        
    def register_cancellable(self, callback: Callable[[], None]) -> None:
        """Register a callback (like task.cancel()) to be invoked upon kill switch activation."""
        self._cancellation_callbacks.append(callback)
        
    async def _on_kill_switch(self, event: KillSwitchActivated) -> None:
        """Handle the kill switch activation."""
        if self._activated:
            return
            
        self._activated = True
        logger.critical(f"[KillSwitch] ACTIVATED! Source: {event.source}, Reason: {event.reason}")
        
        # Invoke all cancellation callbacks
        for callback in self._cancellation_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"[KillSwitch] Error during cancellation callback: {e}")
                
        # Emit ExecutionCancelled
        await self.event_bus.publish(ExecutionCancelled(reason=event.reason))
        
    def is_activated(self) -> bool:
        return self._activated
