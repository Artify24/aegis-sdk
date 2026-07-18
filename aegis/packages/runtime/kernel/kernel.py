from __future__ import annotations
from typing import Optional
from packages.config import AegisConfig
from packages.context import ExecutionContext
from packages.runtime.kernel.state import State
from packages.models import ExecutionResult
from packages.runtime.graph import build_agent_graph
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from packages.runtime.hooks.base import HookManager
from packages.layers.layer1.stages.request_analyzer import RequestAnalyzerStage
from packages.layers.layer1.stages.memory_validation import MemoryValidationStage
from packages.runtime.hooks.base import HookManager

from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.events.models import ExecutionStarted, ExecutionFinished, ExecutionFailed
from packages.runtime.managers.tracker import ExecutionTracker
from packages.runtime.managers.supervisor import ExecutionSupervisor
from packages.runtime.managers.monitor import BehaviorMonitor
from packages.runtime.managers.kill_switch import KillSwitchManager
from typing import Any

from dotenv import load_dotenv
load_dotenv()
from packages.observability.models import (
    ExecutionReport, ExecutionStatus, ErrorReport, ReportContext,
    GovernanceReport, ValidatorResult, ToolCallRecord, ExecutionPlanStep,
    SecurityReport, SDKInfo, AuditInfo, PrivacyInfo,
)
from packages.policy.base import PolicyViolationError, ApprovalRequiredError
from langchain_core.messages import AIMessage, ToolMessage
from datetime import datetime, timezone
import time
import traceback

class RuntimeKernel:
    """
    Core runtime orchestrator for Aegis.
    Responsible for initializing and coordinating all runtime
    components such as the planner, executor, memory,
    providers, and telemetry.
    """

    def __init__(self, config: AegisConfig, memory: Optional[Any] = None, execution_store: Optional[Any] = None) -> None:
            self.config = config
            self.memory = memory
            self.execution_store = execution_store
            self.graph: Optional[CompiledStateGraph] = None
            self.llm: Optional[ChatGroq] = None
            self.hook_manager = HookManager()
            self.event_bus = RuntimeEventBus()
            self.kill_switch = KillSwitchManager(self.event_bus)
            self.monitor = BehaviorMonitor(self.event_bus)
            
            self.layer1_stages = []
            self.initialized = False

    async def initialize(self) -> None:
            """
            Initialize all runtime components.
            Initialize all runtime components and construct the agent graph.
            """
            self.llm = ChatGroq(
                model=self.config.model, 
                temperature=self.config.temperature, 
                max_tokens=self.config.max_tokens
            )
            
            # Initialize Layer 1 pipeline
            self.layer1_stages = [
                RequestAnalyzerStage(available_tools=self.config.tools or []),
                MemoryValidationStage()
            ]
            
            # Bind tools if provided in config
            if self.config.tools:
                self.llm = self.llm.bind_tools(self.config.tools)


            # Configure Fallback Model if provided
            fallback_llm = None
            if self.config.fallback_model:
                fallback_llm = ChatGroq(
                    model=self.config.fallback_model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                if self.config.tools:
                    fallback_llm = fallback_llm.bind_tools(self.config.tools)

            # 2. Initialize LangGraph memory
            if self.memory is None:
                self.memory = MemorySaver()

            # 3. Build the Agent Graph
            self.graph = build_agent_graph(
                llm=self.llm, 
                tools=self.config.tools, 
                memory=self.memory, 
                event_bus=self.event_bus,
                hook_manager=self.hook_manager,
                fallback_llm=fallback_llm,
                timeout_seconds=self.config.timeout_seconds
            )

            self.initialized = True


    async def execute(self, context: ExecutionContext) -> ExecutionResult:
            """
            Execute a single agent request.
            Produces a comprehensive ExecutionReport regardless of success or failure.
            """

            if not self.initialized:
                raise RuntimeError("Kernel has not been initialized.")

            # ── §2 Context + §10 SDK + §12 Audit ────────────────────────
            now_iso = datetime.now(timezone.utc).isoformat()

            report = ExecutionReport(
                context=ReportContext(
                    execution_id=context.execution_id,
                    correlation_id=context.correlation_id,
                    environment=context.environment,
                    sdk_version=context.sdk_version,
                    runtime_version=context.runtime_version,
                    project_id=context.project_name,
                ),
                prompt=context.request.prompt,
                status=ExecutionStatus.PENDING,
                sdk=SDKInfo(version=context.sdk_version, provider="Groq"),
                audit=AuditInfo(
                    created_at=now_iso,
                    policy_version="1.0",
                    sdk_version=context.sdk_version,
                ),
            )

            report.add_timeline_event("Runtime", "Execution Started")
            start_time = time.time()

            try:
                # ── Memory Retrieval ─────────────────────────────────────
                # Use correlation_id (stable session ID) so the graph retains memory
                # across multiple messages. execution_id is unique per-report for telemetry only.
                graph_thread_id = context.correlation_id or context.execution_id
                thread_config = {"configurable": {"thread_id": graph_thread_id}}
                try:
                    graph_state = self.graph.get_state(thread_config)
                    if graph_state and hasattr(graph_state, 'values') and 'messages' in graph_state.values:
                        context.state["recent_messages"] = graph_state.values["messages"][-4:]
                        report.metrics.resources.memory_reads += 1
                except Exception:
                    pass

                # ── Layer 1: Request Intelligence ────────────────────────
                report.add_timeline_event("Layer1", "Analysis Started")
                layer1_start = time.time()
                try:
                    for stage in self.layer1_stages:
                        await stage.process(context)

                    # Populate Layer 1 report
                    report.layer1.detected_intent = context.layer1.intent
                    report.layer1.task_category = context.layer1.task_category
                    report.layer1.capability_detection = list(context.layer1.capabilities)
                    report.layer1.allowed_tools = list(context.layer1.allowed_tools)
                    report.layer1.risk_level = context.layer1.risk_level
                    report.layer1.risk_score = context.layer1.risk_score
                    report.layer1.validation_result = dict(context.layer1.validation_result)

                    report.add_timeline_event("Layer1", "Validation Passed")

                except Exception as e:
                    report.layer1.validation_result = {"error": str(e)}
                    report.add_timeline_event("Layer1", f"Validation Failed: {type(e).__name__}")

                    from packages.layers.layer1.exceptions import PromptValidationError
                    if isinstance(e, PromptValidationError):
                        report.status = ExecutionStatus.FAILED
                        report.error = ErrorReport(
                            type="PromptValidationError",
                            message=str(e),
                            failure_reason="Layer 1 blocked unsafe prompt.",
                        )
                        # §9 Security
                        report.security.policy_violations.append(str(e))
                    raise
                finally:
                    report.metrics.performance.layer1_latency_ms = (time.time() - layer1_start) * 1000
                    report.metrics.resources.llm_calls += 1  # Layer 1 analyzer LLM call

                # ── §9 Security (populate from Layer 1) ──────────────────
                report.security.risk_level = context.layer1.risk_level
                report.security.risk_score = context.layer1.risk_score

                # ── Layer 3: Runtime Control Plane ───────────────────────
                tracker = ExecutionTracker(self.event_bus, agent_id="aegis-agent")
                supervisor = ExecutionSupervisor(self.event_bus, context)

                try:
                    # Hooks (includes NL Policy evaluation)
                    report.add_timeline_event("Layer2", "Governance Started")
                    await self.hook_manager.before_execution(context)
                    report.add_timeline_event("Layer2", "Authorization Passed")
                    await self.event_bus.publish(ExecutionStarted(prompt=context.request.prompt))

                    # §3 Planner info
                    report.planner.provider = "Groq"
                    report.planner.model = self.config.model

                    # Serialize Layer1 context for the graph
                    thread_config = {"configurable": {"thread_id": graph_thread_id}}
                    l1_dict = {}
                    if hasattr(context, "layer1"):
                        l1_dict = {
                            "intent": context.layer1.intent,
                            "task_category": context.layer1.task_category,
                            "capabilities": context.layer1.capabilities,
                            "allowed_tools": context.layer1.allowed_tools,
                            "validation_result": context.layer1.validation_result,
                            "risk_level": context.layer1.risk_level,
                            "risk_score": context.layer1.risk_score,
                            "risk_factors": context.layer1.risk_factors,
                            "execution_recommendation": context.layer1.execution_recommendation,
                        }

                    inputs = {
                        "messages": [HumanMessage(content=context.request.prompt)],
                        "layer1_context": l1_dict,
                        "behavior_state": context.state.get("behavior_state"),
                    }

                    # ── Invoke the LangGraph planner ─────────────────────
                    report.add_timeline_event("Planner", "Planning Started")
                    planner_start = time.time()
                    final_state = await self.graph.ainvoke(inputs, config=thread_config)
                    planner_elapsed = (time.time() - planner_start) * 1000
                    report.metrics.performance.planner_latency_ms = planner_elapsed
                    report.planner.latency_ms = planner_elapsed
                    report.add_timeline_event("Planner", "Planning Finished")

                    # ── §4/§5 Extract Execution Plan + Tool Calls ───────
                    # Use REAL telemetry from ExecutorNode via State
                    tool_telemetry = final_state.get("tool_telemetry", [])
                    total_tool_latency = 0.0

                    for entry in tool_telemetry:
                        report.tool_calls.append(ToolCallRecord(
                            tool_call_id=entry.get("tool_call_id", ""),
                            tool=entry.get("tool", "unknown"),
                            category=entry.get("category", "general"),
                            status=entry.get("status", "UNKNOWN"),
                            started_at=entry.get("started_at"),
                            finished_at=entry.get("finished_at"),
                            duration_ms=entry.get("duration_ms", 0.0),
                            retry_count=entry.get("retry_count", 0),
                            input_summary=entry.get("input_summary", ""),
                            output_summary=entry.get("output_summary", ""),
                            error=entry.get("error"),
                        ))
                        total_tool_latency += entry.get("duration_ms", 0.0)
                        report.add_timeline_event(
                            "Runtime",
                            f"Tool Executed: {entry.get('tool', 'unknown')}",
                            metadata={
                                "tool_call_id": entry.get("tool_call_id"),
                                "status": entry.get("status"),
                                "duration_ms": entry.get("duration_ms", 0.0),
                            },
                        )

                    report.metrics.performance.tool_latency_ms = round(total_tool_latency, 2)
                    report.metrics.resources.tool_calls = len(tool_telemetry)

                    # Build execution plan from AIMessage tool_calls
                    step_num = 0
                    total_input_tokens = 0
                    total_output_tokens = 0

                    for msg in final_state["messages"]:
                        if isinstance(msg, AIMessage):
                            report.metrics.resources.llm_calls += 1

                            # Extract real token usage from response_metadata
                            resp_meta = getattr(msg, "response_metadata", {}) or {}
                            usage = resp_meta.get("token_usage") or resp_meta.get("usage", {})
                            if usage:
                                total_input_tokens += usage.get("prompt_tokens", 0)
                                total_output_tokens += usage.get("completion_tokens", 0)

                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                report.planner.planning_iterations += 1
                                for tc in msg.tool_calls:
                                    step_num += 1
                                    tool_name = tc.get("name", "unknown")
                                    args = tc.get("args", {})
                                    arg_keys = list(args.keys())[:3]
                                    purpose_hint = ", ".join(arg_keys)
                                    report.execution_plan.append(ExecutionPlanStep(
                                        step=step_num,
                                        tool=tool_name,
                                        purpose=f"Execute {tool_name}" + (f" ({purpose_hint})" if purpose_hint else ""),
                                    ))

                    # Populate token metrics
                    report.planner.input_tokens = total_input_tokens
                    report.planner.output_tokens = total_output_tokens
                    report.planner.total_tokens = total_input_tokens + total_output_tokens
                    report.metrics.cost.input_tokens = total_input_tokens
                    report.metrics.cost.output_tokens = total_output_tokens
                    report.metrics.cost.total_tokens = total_input_tokens + total_output_tokens

                    # Total LLM calls for planner
                    report.planner.total_llm_calls = report.metrics.resources.llm_calls

                    # Extract final AI message
                    last_message = final_state["messages"][-1]

                    result = ExecutionResult(
                        output=last_message.content,
                        tool_calls=[tc.tool for tc in report.tool_calls],
                        tokens_used=report.planner.total_tokens,
                        execution_time=planner_elapsed,
                        metadata={"layer1": context.layer1},
                    )

                    await self.hook_manager.after_execution(context, result)
                    await self.event_bus.publish(ExecutionFinished(result=last_message.content))

                    # ── §6 Governance (success path) ─────────────────────
                    report.governance.decision = "ALLOW"
                    report.governance.authorization_result = "PASS"
                    report.governance.policy_result = "PASS"
                    report.governance.validators = [
                        ValidatorResult(name="Identity Validator", status="PASS"),
                        ValidatorResult(name="Permission Validator", status="PASS"),
                        ValidatorResult(name="Tool Authorization", status="PASS"),
                        ValidatorResult(name="Policy Engine", status="PASS"),
                    ]

                    report.status = ExecutionStatus.SUCCESS
                    report.output = result.output
                    report.add_timeline_event("Runtime", "Execution Completed Successfully")

                    return result

                except ApprovalRequiredError as e:
                    report.status = ExecutionStatus.BLOCKED
                    report.governance.decision = "APPROVAL_REQUIRED"
                    report.governance.authorization_result = "PENDING"
                    report.governance.approval_required = True
                    report.governance.approval_status = "PENDING"
                    report.governance.policy_result = "APPROVAL_REQUIRED"
                    report.governance.validators = [
                        ValidatorResult(name="Identity Validator", status="PASS"),
                        ValidatorResult(name="Permission Validator", status="PASS"),
                        ValidatorResult(name="Tool Authorization", status="PASS"),
                        ValidatorResult(name="Policy Engine", status="APPROVAL_REQUIRED", reason=str(e)),
                    ]
                    report.security.approval_required = True
                    report.error = ErrorReport(
                        type="ApprovalRequiredError",
                        message=str(e),
                        failure_reason="Human-in-the-loop approval required.",
                    )
                    report.add_timeline_event(
                        "Layer2",
                        "Governance Decision: APPROVAL_REQUIRED",
                        metadata={"reason": str(e)[:200]},
                    )
                    raise

                except PolicyViolationError as e:
                    report.status = ExecutionStatus.BLOCKED
                    report.governance.decision = "DENY"
                    report.governance.authorization_result = "FAIL"
                    report.governance.policy_result = "VIOLATION"
                    report.governance.failed_validator = "Policy Engine"
                    report.governance.failure_reason = str(e)
                    report.governance.validators = [
                        ValidatorResult(name="Identity Validator", status="PASS"),
                        ValidatorResult(name="Permission Validator", status="PASS"),
                        ValidatorResult(name="Tool Authorization", status="FAIL", reason=str(e)),
                        ValidatorResult(name="Policy Engine", status="FAIL", reason=str(e)),
                    ]
                    report.security.policy_violations.append(str(e))
                    report.error = ErrorReport(
                        type="PolicyViolationError",
                        message=str(e),
                        failure_reason="Policy violation blocked execution.",
                    )
                    report.add_timeline_event(
                        "Layer2",
                        "Governance Decision: DENY",
                        metadata={"reason": str(e)[:200]},
                    )
                    raise

                except Exception as e:
                    report.status = ExecutionStatus.FAILED
                    report.error = ErrorReport(
                        type=e.__class__.__name__,
                        message=str(e),
                        traceback=traceback.format_exc(),
                        failure_reason="Internal Execution Error",
                    )
                    report.add_timeline_event("Runtime", f"Error: {e.__class__.__name__}")
                    raise

                finally:
                    tracker.cleanup()
                    supervisor.cleanup()

            except Exception as outer_e:
                if report.status == ExecutionStatus.PENDING:
                    report.status = ExecutionStatus.FAILED
                    report.error = ErrorReport(
                        type=outer_e.__class__.__name__,
                        message=str(outer_e),
                        traceback=traceback.format_exc(),
                        failure_reason="Execution Aborted",
                    )
                raise

            finally:
                # ── Finalise all report sections ─────────────────────────
                elapsed = (time.time() - start_time) * 1000
                report.metrics.performance.total_latency_ms = round(elapsed, 2)

                # §3 Planner: round latency
                report.planner.latency_ms = round(report.planner.latency_ms, 2)

                # Ensure all states are internally consistent before scoring
                report.ensure_consistency()

                # §8 Execution Graph (for dashboard visualisation)
                report.build_execution_graph()

                # §13 Governance Score (deterministic, after consistency fix)
                report.compute_governance_score()

                # §1 Summary (last — reflects final consistent state)
                report.compute_summary()

                report.add_timeline_event("Runtime", "Report Finalised")

                # Always persist
                if self.execution_store:
                    self.execution_store.save(report)

    async def shutdown(self) -> None:
            """
            Shutdown runtime resources.
            """
            self.graph = None
            self.memory = None
            self.initialized = False