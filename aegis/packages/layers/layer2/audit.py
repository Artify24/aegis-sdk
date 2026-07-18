import logging
from packages.models import ExecutionMetadata, BehaviorState
from packages.context import ExecutionContext

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Handles feedback from Runtime execution (Layer 3) and updates the BehaviorState
    for future Layer 2 governance evaluations.
    """
    def log_execution(self, metadata: ExecutionMetadata, context: ExecutionContext) -> None:
        """
        Record the outcome of a tool execution.
        """
        logger.info(f"Layer 2 Audit: Recording execution metadata for {metadata.tool_name}")
        
        # Ensure behavior state exists in context
        if "behavior_state" not in context.state or not isinstance(context.state["behavior_state"], BehaviorState):
            context.state["behavior_state"] = BehaviorState()
            
        state: BehaviorState = context.state["behavior_state"]
        
        # Track counts
        state.call_counts[metadata.tool_name] = state.call_counts.get(metadata.tool_name, 0) + 1
        
        # Track failures for runaway retry prevention
        if not metadata.success:
            state.consecutive_failures += 1
            logger.warning(f"Layer 2 Audit: Consecutive failures incremented to {state.consecutive_failures}")
        else:
            state.consecutive_failures = 0
            
        # Track metrics
        state.total_execution_time_ms += metadata.execution_time_ms
        state.history.append(metadata)
        
        logger.debug(f"Layer 2 Audit: Tool '{metadata.tool_name}' execution recorded. Success: {metadata.success}")
