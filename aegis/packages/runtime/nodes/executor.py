from typing import Sequence, Any
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone

from langchain_core.tools import BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from packages.runtime.kernel.state import State

from packages.models import ProposedAction, GovernanceResult, ExecutionMetadata, NormalizedExecutionResult
from packages.layers.layer2.engine import GovernanceEngine

from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.events.models import ToolStarted, ToolFinished
from packages.runtime.managers.registry import ToolRegistry
from packages.runtime.managers.executor import ToolExecutor
from packages.runtime.managers.retry import RetryManager
from packages.runtime.managers.timeout import TimeoutManager
from packages.runtime.managers.normalizer import ResultNormalizer
from packages.runtime.hooks.base import HookManager
from packages.context import ExecutionContext

logger = logging.getLogger(__name__)

class ExecutorNode:
    """
    The Executor node bridges Layer 2 and Layer 3.
    It takes tool calls from the Planner, proposes them to the Layer 2 Governance Engine,
    and if approved, executes them securely via Layer 3 Runtime Managers.
    """
    def __init__(self, tools: Sequence[BaseTool], event_bus: RuntimeEventBus = None, hook_manager: HookManager = None, timeout_seconds: int = 30):
        self.event_bus = event_bus
        self.hook_manager = hook_manager
        
        # Layer 2
        self.governance_engine = GovernanceEngine()
        
        # Layer 3 Managers (Fully Integrated Architecture)
        self.registry = ToolRegistry()
        for tool in tools:
            # We assume tools might not have strongly-typed metadata yet at this level,
            # so the registry uses extraction fallback.
            self.registry.register_tool(tool)
            
        self.executor = ToolExecutor(self.registry)
        self.retry_manager = RetryManager()
        self.timeout_manager = TimeoutManager()
        self.normalizer = ResultNormalizer()
        
        self.default_timeout = timeout_seconds

    async def __call__(self, state: State, config: RunnableConfig | None = None):
        messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
        last_message = messages[-1] if messages else None
        
        if not last_message or not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return {"messages": []}
            
        # Context Reconstruction
        from packages.context import ExecutionContext, Layer1Context
        from packages.models import AgentRequest
        
        layer1_dict = state.get("layer1_context", {}) if isinstance(state, dict) else getattr(state, "layer1_context", {})
        layer1_ctx = Layer1Context(**layer1_dict) if layer1_dict else Layer1Context()
        
        state_dict = dict(state) if isinstance(state, dict) else (state.model_dump() if hasattr(state, "model_dump") else dict(state))
        
        behavior_state = state.get("behavior_state") if isinstance(state, dict) else getattr(state, "behavior_state", None)
        if behavior_state:
            state_dict["behavior_state"] = behavior_state
            
        exec_ctx = ExecutionContext(request=AgentRequest(prompt=""), layer1=layer1_ctx, state=state_dict)

        results = []
        telemetry_entries = []
        # Phase 3.9 Global Execution ID
        global_execution_id = str(uuid.uuid4())
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            # 1. Convert to ProposedAction
            action = ProposedAction(tool_name=tool_name, arguments=tool_args)
            
            if self.event_bus:
                await self.event_bus.publish(ToolStarted(tool_name=tool_name, arguments=tool_args))
            
            # 2. Layer 2 Governance
            gov_result: GovernanceResult = await self.governance_engine.evaluate(action, exec_ctx)
            
            if not gov_result.approved:
                blocked_content = f"Execution blocked by Layer 2 Governance. Reason: {gov_result.failure_reason}"
                results.append(ToolMessage(
                    content=blocked_content,
                    name=tool_name,
                    tool_call_id=tool_id
                ))
                telemetry_entries.append({
                    "tool_call_id": tool_id,
                    "tool": tool_name,
                    "category": self._infer_category(tool_name),
                    "status": "BLOCKED",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": 0.0,
                    "retry_count": 0,
                    "input_summary": self._summarize_input(tool_name, tool_args),
                    "output_summary": f"Blocked by governance: {gov_result.failure_reason}",
                    "error": gov_result.failure_reason,
                })
                continue
                
            # 3. Layer 3 Runtime Execution
            try:
                registered_tool = self.registry.get_tool(tool_name)
                retry_policy = registered_tool.metadata.retry_policy
                timeout = registered_tool.metadata.timeout_seconds
            except Exception as e:
                error_content = f"Error: Tool {tool_name} not found in Registry."
                results.append(ToolMessage(
                    content=error_content,
                    name=tool_name,
                    tool_call_id=tool_id
                ))
                telemetry_entries.append({
                    "tool_call_id": tool_id,
                    "tool": tool_name,
                    "category": self._infer_category(tool_name),
                    "status": "FAILED",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": 0.0,
                    "retry_count": 0,
                    "input_summary": self._summarize_input(tool_name, tool_args),
                    "output_summary": error_content,
                    "error": str(e),
                })
                continue
                
            started_at = datetime.now(timezone.utc).isoformat()
            start_time = time.time()
            
            # Encapsulate timeout boundary
            async def timed_execution(action):
                return await self.timeout_manager.execute_with_timeout(
                    self.executor.execute,
                    timeout_seconds=timeout,
                    fallback_name=tool_name,
                    action=action
                )
                
            # Execute with Retry
            result, metadata = await self.retry_manager.execute_with_retry(
                timed_execution,
                retry_policy=retry_policy,
                action=action
            )
            
            end_time = time.time()
            finished_at = datetime.now(timezone.utc).isoformat()
            duration_ms = (end_time - start_time) * 1000
            
            # Phase 3.9: Populate Telemetry Metadata
            metadata.action_id = tool_id
            metadata.execution_id = global_execution_id
            metadata.start_time = start_time
            metadata.end_time = end_time
            metadata.status = "completed" if metadata.success else "failed"

            # 4. Normalize Result
            normalized: NormalizedExecutionResult = self.normalizer.normalize((result, metadata))
            
            if self.event_bus:
                await self.event_bus.publish(ToolFinished(
                    tool_name=tool_name, 
                    success=metadata.success, 
                    result=normalized.output,
                    execution_time_ms=metadata.execution_time_ms
                ))
            
            # 5. Collect telemetry
            telemetry_entries.append({
                "tool_call_id": tool_id,
                "tool": tool_name,
                "category": self._infer_category(tool_name),
                "status": "SUCCESS" if metadata.success else "FAILED",
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_ms": round(duration_ms, 2),
                "retry_count": metadata.retries_attempted,
                "input_summary": self._summarize_input(tool_name, tool_args),
                "output_summary": self._summarize_output(tool_name, normalized.output),
                "error": metadata.exception_details if not metadata.success else None,
            })
            
            # Return to state
            results.append(ToolMessage(
                content=normalized.output,
                name=tool_name,
                tool_call_id=tool_id
            ))
            
        # Merge telemetry with existing entries from prior iterations
        existing_telemetry = state.get("tool_telemetry", []) if isinstance(state, dict) else getattr(state, "tool_telemetry", [])
        merged_telemetry = list(existing_telemetry) + telemetry_entries

        return {
            "messages": results,
            "behavior_state": exec_ctx.state.get("behavior_state"),
            "tool_telemetry": merged_telemetry,
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _infer_category(tool_name: str) -> str:
        """Infer tool category from its name prefix."""
        prefixes = {
            "github_": "github",
            "db_": "database",
            "email_": "email",
            "browser_": "browser",
            "file_": "filesystem",
            "search_": "search",
        }
        for prefix, category in prefixes.items():
            if tool_name.startswith(prefix):
                return category
        return "general"

    @staticmethod
    def _summarize_input(tool_name: str, args: dict) -> str:
        """Generate a concise human-readable input summary. Never expose secrets."""
        try:
            parts = []
            for key, val in list(args.items())[:4]:
                key_lower = key.lower()
                if any(s in key_lower for s in ("password", "token", "secret", "key", "api")):
                    continue
                val_str = str(val)
                if len(val_str) > 80:
                    val_str = val_str[:77] + "..."
                parts.append(f"{key}={val_str}")
            return ", ".join(parts) if parts else "(no args)"
        except Exception:
            return "(unable to summarize)"

    @staticmethod
    def _summarize_output(tool_name: str, raw_output: str) -> str:
        """Generate a concise human-readable output summary from raw JSON."""
        import json as _json
        try:
            data = _json.loads(raw_output)
            status = data.get("status", "")

            # Database tools
            if tool_name.startswith("db_"):
                if "data" in data and isinstance(data["data"], list):
                    count = len(data["data"])
                    return f"Retrieved {count} row{'s' if count != 1 else ''} from database"
                if "rows_affected" in data:
                    return f"{data['rows_affected']} row(s) affected"
                if "message" in data:
                    return data["message"]
                return f"Database operation {status}"

            # GitHub tools
            if tool_name.startswith("github_"):
                if "issues" in data and isinstance(data["issues"], list):
                    return f"Retrieved {len(data['issues'])} GitHub issues"
                if "repositories" in data and isinstance(data["repositories"], list):
                    return f"Retrieved {len(data['repositories'])} repositories"
                if "message" in data:
                    return data["message"]
                return f"GitHub operation {status}"

            # Email tools
            if tool_name.startswith("email_"):
                if "message" in data:
                    return data["message"]
                return f"Email operation {status}"

            # Generic fallback
            if "message" in data:
                msg = data["message"]
                return msg[:200] if len(msg) > 200 else msg
            return f"Operation completed ({status})" if status else raw_output[:150]

        except (_json.JSONDecodeError, AttributeError):
            # Not JSON — return truncated text
            return raw_output[:150] if raw_output else "(empty response)"
