from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time

@dataclass
class RuntimeEvent:
    """Base class for all runtime events."""
    trace_id: str = ""
    execution_id: str = ""
    request_id: str = ""
    step_id: str = ""
    parent_step: str = ""
    agent_id: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Execution Lifecycle Events ---
@dataclass
class ExecutionStarted(RuntimeEvent):
    prompt: str = ""

@dataclass
class ExecutionFinished(RuntimeEvent):
    result: str = ""

@dataclass
class ExecutionFailed(RuntimeEvent):
    error: str = ""

@dataclass
class ExecutionCancelled(RuntimeEvent):
    reason: str = ""

# --- Planner Events ---
@dataclass
class PlannerStepStarted(RuntimeEvent):
    pass

@dataclass
class PlannerStepFinished(RuntimeEvent):
    decision: str = ""
    reasoning: str = ""

# --- Tool Events ---
@dataclass
class ToolStarted(RuntimeEvent):
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolFinished(RuntimeEvent):
    tool_name: str = ""
    success: bool = True
    result: str = ""
    execution_time_ms: float = 0.0

# --- Provider Events ---
@dataclass
class ProviderStarted(RuntimeEvent):
    provider_name: str = ""

@dataclass
class ProviderFinished(RuntimeEvent):
    provider_name: str = ""
    success: bool = True

# --- Memory Events ---
@dataclass
class MemoryRead(RuntimeEvent):
    namespace: str = ""
    key: str = ""

@dataclass
class MemoryWrite(RuntimeEvent):
    namespace: str = ""
    key: str = ""

# --- Sub-Agent Events ---
@dataclass
class AgentSpawned(RuntimeEvent):
    child_agent_id: str = ""
    purpose: str = ""

@dataclass
class AgentFinished(RuntimeEvent):
    child_agent_id: str = ""

# --- Resilience Events ---
@dataclass
class RetryStarted(RuntimeEvent):
    attempt: int = 1
    reason: str = ""

@dataclass
class RetryCompleted(RuntimeEvent):
    attempt: int = 1
    success: bool = True

@dataclass
class TimeoutOccurred(RuntimeEvent):
    component: str = ""
    timeout_seconds: float = 0.0

@dataclass
class KillSwitchActivated(RuntimeEvent):
    source: str = ""
    reason: str = ""
