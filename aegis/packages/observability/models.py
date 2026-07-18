"""
Aegis SDK — Execution Report Models (v3 Production)

Production-grade execution telemetry for enterprise debugging,
governance auditing, runtime observability, and Aegis Cloud Dashboard.

Every field exists for a clear operational reason.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime, timezone
import platform
import sys
import time


# ── Enums ────────────────────────────────────────────────────────────────────

class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


# ── §1 Execution Summary ────────────────────────────────────────────────────

@dataclass
class ExecutionSummary:
    """Top-level summary for dashboard listing pages."""
    status: str = "PENDING"
    risk_level: str = "UNKNOWN"
    governance: str = "PENDING"
    duration_ms: float = 0.0
    tools_used: int = 0
    approval_required: bool = False


# ── §2 Report Context ───────────────────────────────────────────────────────

@dataclass
class ReportContext:
    """Runtime metadata for tracing, multi-tenant routing, and multi-agent."""
    workspace_id: str = ""
    project_id: str = ""
    execution_id: str = ""
    correlation_id: str = ""
    environment: str = "development"
    sdk_version: str = "0.1.0"
    runtime_version: str = "1.0.0"
    # §5 Multi-agent support (schema only — not implemented yet)
    parent_execution_id: Optional[str] = None
    root_execution_id: Optional[str] = None


# ── Layer 1 Report ──────────────────────────────────────────────────────────

@dataclass
class Layer1Report:
    """Results from the Layer 1 Request Intelligence pipeline."""
    validation_result: Dict[str, Any] = field(default_factory=dict)
    detected_intent: Optional[str] = None
    task_category: Optional[str] = None
    capability_detection: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    risk_level: str = "UNKNOWN"
    risk_score: float = 0.0


# ── §3 Planner Report ──────────────────────────────────────────────────────

@dataclass
class PlannerReport:
    """Runtime information about the LLM planner."""
    provider: str = "unknown"
    model: str = "unknown"
    total_llm_calls: int = 0
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    planning_iterations: int = 0


# ── §4 Execution Plan ──────────────────────────────────────────────────────

@dataclass
class ExecutionPlanStep:
    """A single step in the planner's structured execution plan."""
    step: int = 0
    tool: str = ""
    purpose: str = ""


# ── §5 Tool Call Record ─────────────────────────────────────────────────────

@dataclass
class ToolCallRecord:
    """
    Rich telemetry for a single tool invocation.
    Populated by the ExecutorNode via tool_telemetry in LangGraph State.
    """
    tool_call_id: str = ""
    tool: str = ""
    category: str = "general"
    status: str = "PENDING"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: float = 0.0
    retry_count: int = 0
    input_summary: str = ""
    output_summary: str = ""
    error: Optional[str] = None


# ── §6 Governance Report ────────────────────────────────────────────────────

@dataclass
class ValidatorResult:
    """Result from a single governance validator."""
    name: str = ""
    status: str = "PENDING"
    reason: Optional[str] = None


@dataclass
class GovernanceReport:
    """Layer 2 Execution Governance results."""
    decision: str = "PENDING"
    authorization_result: str = "PENDING"
    policy_result: str = "PENDING"
    approval_required: bool = False
    approval_status: str = "NONE"
    validators: List[ValidatorResult] = field(default_factory=list)
    failed_validator: Optional[str] = None
    failure_reason: Optional[str] = None


# ── §7 Execution Timeline ──────────────────────────────────────────────────

@dataclass
class TimelineEvent:
    """A single timestamped event in the execution lifecycle."""
    timestamp: str = ""
    layer: str = ""
    event: str = ""
    metadata: Optional[Dict[str, Any]] = None


# ── §8 Metrics ──────────────────────────────────────────────────────────────

@dataclass
class PerformanceMetrics:
    """Latency measurements across the execution pipeline."""
    total_latency_ms: float = 0.0
    layer1_latency_ms: float = 0.0
    layer2_latency_ms: float = 0.0
    planner_latency_ms: float = 0.0
    tool_latency_ms: float = 0.0


@dataclass
class ResourceMetrics:
    """Resource consumption counters."""
    llm_calls: int = 0
    tool_calls: int = 0
    memory_reads: int = 0
    memory_writes: int = 0


@dataclass
class CostMetrics:
    """Token usage and estimated cost."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class ExecutionMetrics:
    """Aggregated metrics split into logical groups."""
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    resources: ResourceMetrics = field(default_factory=ResourceMetrics)
    cost: CostMetrics = field(default_factory=CostMetrics)


# ── §9 Security Report ──────────────────────────────────────────────────────

@dataclass
class SecurityReport:
    """Runtime security information for auditing."""
    risk_level: str = "UNKNOWN"
    risk_score: float = 0.0
    blocked_tools: List[str] = field(default_factory=list)
    blocked_actions: List[str] = field(default_factory=list)
    policy_violations: List[str] = field(default_factory=list)
    approval_required: bool = False
    approval_given: bool = False


# ── §10 SDK Information ─────────────────────────────────────────────────────

@dataclass
class SDKInfo:
    """Runtime environment metadata."""
    version: str = "0.1.0"
    provider: str = "Groq"
    python: str = field(default_factory=lambda: f"{sys.version_info.major}.{sys.version_info.minor}")
    os: str = field(default_factory=lambda: platform.system())


# ── §11 Error Report ────────────────────────────────────────────────────────

@dataclass
class ErrorReport:
    """Structured error information."""
    type: Optional[str] = None
    message: Optional[str] = None
    traceback: Optional[str] = None
    failure_reason: Optional[str] = None


# ── §12 Audit Information ───────────────────────────────────────────────────

@dataclass
class AuditInfo:
    """Compliance and audit metadata."""
    created_at: Optional[str] = None
    stored_at: Optional[str] = None
    policy_version: str = "1.0"
    sdk_version: str = "0.1.0"


# ── §6 Privacy ──────────────────────────────────────────────────────────────

@dataclass
class PrivacyInfo:
    """Indicates whether the report contains or has redacted PII."""
    contains_pii: bool = False
    redacted: bool = False


# ── §8 Execution Graph ─────────────────────────────────────────────────────

@dataclass
class ExecutionGraphNode:
    """A node in the lightweight execution graph."""
    id: str = ""
    label: str = ""
    layer: str = ""
    status: str = "PENDING"


@dataclass
class ExecutionGraphEdge:
    """An edge in the lightweight execution graph."""
    source: str = ""
    target: str = ""


@dataclass
class ExecutionGraph:
    """Lightweight DAG for dashboard visualization."""
    nodes: List[ExecutionGraphNode] = field(default_factory=list)
    edges: List[ExecutionGraphEdge] = field(default_factory=list)


# ── §13 Governance Score ────────────────────────────────────────────────────

@dataclass
class ScoreBreakdown:
    """
    Detailed breakdown of governance quality score.

    Scoring methodology (deterministic, measurable):
    ─────────────────────────────────────────────────
    request_validation  (20 pts)  — 20 if Layer 1 is_safe=True, else 0.
    least_privilege     (20 pts)  — 20 if tools_used ≤ tools_allowed, else 10.
    policy_compliance   (20 pts)  — 20 if policy PASS/PENDING, 0 if VIOLATION.
    tool_authorization  (20 pts)  — 20 if authorization PASS/PENDING, 0 if FAIL.
    runtime_integrity   (20 pts)  — 20 if SUCCESS, 5 if FAILED, 10 otherwise.
                                    Capped at 15 for HIGH risk, 10 for CRITICAL.
    """
    request_validation: int = 0
    least_privilege: int = 0
    policy_compliance: int = 0
    tool_authorization: int = 0
    runtime_integrity: int = 0


@dataclass
class GovernanceScore:
    """Internal governance quality score for observability."""
    score: int = 0
    max_score: int = 100
    breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    warnings: List[str] = field(default_factory=list)


# ── Main Execution Report ───────────────────────────────────────────────────

@dataclass
class ExecutionReport:
    """
    The canonical record of an Aegis runtime execution.

    Designed to be immediately consumable by the future Aegis Cloud
    backend and dashboard without requiring structural changes.
    """

    # §1 — Summary (dashboard listing)
    summary: ExecutionSummary = field(default_factory=ExecutionSummary)

    # §2 — Context (runtime metadata + multi-agent)
    context: ReportContext = field(default_factory=ReportContext)

    # Request
    prompt: str = ""

    # Layer 1 — Request Intelligence
    layer1: Layer1Report = field(default_factory=Layer1Report)

    # §3 — Planner
    planner: PlannerReport = field(default_factory=PlannerReport)

    # §6 — Governance (Layer 2)
    governance: GovernanceReport = field(default_factory=GovernanceReport)

    # §4 — Execution Plan
    execution_plan: List[ExecutionPlanStep] = field(default_factory=list)

    # §5 — Tool Calls
    tool_calls: List[ToolCallRecord] = field(default_factory=list)

    # §7 — Timeline
    timeline: List[TimelineEvent] = field(default_factory=list)

    # §8 — Metrics
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)

    # §9 — Security
    security: SecurityReport = field(default_factory=SecurityReport)

    # §10 — SDK
    sdk: SDKInfo = field(default_factory=SDKInfo)

    # Output
    output: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING

    # §11 — Error
    error: ErrorReport = field(default_factory=ErrorReport)

    # §12 — Audit
    audit: AuditInfo = field(default_factory=AuditInfo)

    # Privacy
    privacy: PrivacyInfo = field(default_factory=PrivacyInfo)

    # Execution Graph
    execution_graph: ExecutionGraph = field(default_factory=ExecutionGraph)

    # §13 — Governance Score
    governance_score: GovernanceScore = field(default_factory=GovernanceScore)

    # ── Helper Methods ───────────────────────────────────────────────────

    def add_timeline_event(self, layer: str, event: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Append a timestamped event to the execution timeline."""
        self.timeline.append(TimelineEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            layer=layer,
            event=event,
            metadata=metadata,
        ))

    def compute_summary(self) -> None:
        """Compute the top-level summary from collected data. Must be consistent."""
        self.summary.status = self.status.value
        self.summary.risk_level = self.layer1.risk_level
        self.summary.governance = self.governance.decision
        self.summary.duration_ms = round(self.metrics.performance.total_latency_ms, 2)
        self.summary.tools_used = len(self.tool_calls)
        self.summary.approval_required = self.governance.approval_required

    def compute_governance_score(self) -> None:
        """
        Compute the governance quality score.

        Scoring is deterministic and measurable — see ScoreBreakdown docstring.
        """
        breakdown = ScoreBreakdown()
        warnings: List[str] = []

        # request_validation (20 pts): 20 if is_safe=True, else 0
        if self.layer1.validation_result.get("is_safe", False):
            breakdown.request_validation = 20
        else:
            breakdown.request_validation = 0
            warnings.append("Request failed validation")

        # least_privilege (20 pts): 20 if used ≤ allowed, else 10
        allowed_count = len(self.layer1.allowed_tools)
        used_count = len(self.tool_calls)
        if allowed_count == 0 and used_count == 0:
            breakdown.least_privilege = 20
        elif used_count <= allowed_count:
            breakdown.least_privilege = 20
        else:
            breakdown.least_privilege = 10
            warnings.append("Tools used exceeded allowed tools")

        # policy_compliance (20 pts): 20 if PASS/PENDING, 0 if VIOLATION
        if self.governance.policy_result in ("PASS", "PENDING"):
            breakdown.policy_compliance = 20
        elif self.governance.policy_result == "VIOLATION":
            breakdown.policy_compliance = 0
            warnings.append("Policy violation detected")
        else:
            breakdown.policy_compliance = 15

        # tool_authorization (20 pts): 20 if PASS/PENDING, 0 if FAIL
        if self.governance.authorization_result in ("PASS", "PENDING"):
            breakdown.tool_authorization = 20
        else:
            breakdown.tool_authorization = 0
            warnings.append("Tool authorization failed")

        # runtime_integrity (20 pts): 20 if SUCCESS, 5 if FAILED, 10 otherwise
        if self.status == ExecutionStatus.SUCCESS:
            breakdown.runtime_integrity = 20
        elif self.status in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED):
            breakdown.runtime_integrity = 5
            warnings.append("Execution failed or blocked")
        else:
            breakdown.runtime_integrity = 10

        # Risk-level cap on runtime_integrity
        risk = self.layer1.risk_level.upper()
        if risk == "MEDIUM":
            warnings.append("Medium risk request")
        elif risk == "HIGH":
            warnings.append("High risk request")
            breakdown.runtime_integrity = min(breakdown.runtime_integrity, 15)
        elif risk == "CRITICAL":
            warnings.append("Critical risk request")
            breakdown.runtime_integrity = min(breakdown.runtime_integrity, 10)

        total = (
            breakdown.request_validation
            + breakdown.least_privilege
            + breakdown.policy_compliance
            + breakdown.tool_authorization
            + breakdown.runtime_integrity
        )

        self.governance_score = GovernanceScore(
            score=total,
            max_score=100,
            breakdown=breakdown,
            warnings=warnings,
        )

    def build_execution_graph(self) -> None:
        """Build a lightweight execution graph from timeline events."""
        nodes: List[ExecutionGraphNode] = []
        edges: List[ExecutionGraphEdge] = []

        # Fixed infrastructure nodes
        infra = [
            ("layer1", "Layer 1: Analysis", "Layer1"),
            ("governance", "Layer 2: Governance", "Layer2"),
            ("planner", "Planner", "Planner"),
        ]
        for nid, label, layer in infra:
            status = "PASS"
            if nid == "layer1" and not self.layer1.validation_result.get("is_safe", True):
                status = "FAIL"
            if nid == "governance" and self.governance.decision == "DENY":
                status = "FAIL"
            nodes.append(ExecutionGraphNode(id=nid, label=label, layer=layer, status=status))

        edges.append(ExecutionGraphEdge(source="layer1", target="governance"))
        edges.append(ExecutionGraphEdge(source="governance", target="planner"))

        # Tool nodes
        prev_id = "planner"
        for tc in self.tool_calls:
            tid = tc.tool_call_id or tc.tool
            nodes.append(ExecutionGraphNode(id=tid, label=tc.tool, layer="Runtime", status=tc.status))
            edges.append(ExecutionGraphEdge(source=prev_id, target=tid))
            prev_id = tid

        self.execution_graph = ExecutionGraph(nodes=nodes, edges=edges)

    def ensure_consistency(self) -> None:
        """
        Ensure all report states are internally consistent.
        Must be called before serialisation.
        """
        status_val = self.status.value if isinstance(self.status, ExecutionStatus) else self.status

        # Governance consistency
        if self.governance.decision == "ALLOW":
            self.governance.authorization_result = "PASS"
            self.governance.policy_result = "PASS"
        elif self.governance.decision == "DENY":
            if self.governance.authorization_result == "PENDING":
                self.governance.authorization_result = "FAIL"

        # Status consistency
        if self.governance.decision == "DENY" and self.status != ExecutionStatus.BLOCKED:
            self.status = ExecutionStatus.BLOCKED
            status_val = "BLOCKED"

        if self.governance.decision == "APPROVAL_REQUIRED" and self.status == ExecutionStatus.PENDING:
            self.status = ExecutionStatus.BLOCKED
            status_val = "BLOCKED"

        # Summary must match
        self.summary.status = status_val

        # Security blocked_tools from tool_calls
        for tc in self.tool_calls:
            if tc.status == "BLOCKED" and tc.tool not in self.security.blocked_tools:
                self.security.blocked_tools.append(tc.tool)

        # Privacy — simple PII heuristic
        prompt_lower = self.prompt.lower()
        if any(kw in prompt_lower for kw in ("email", "password", "ssn", "credit card", "phone")):
            self.privacy.contains_pii = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert the complete report to a JSON-serializable dictionary."""
        from dataclasses import asdict

        data = asdict(self)

        # Normalise enum values
        status_val = self.status.value if isinstance(self.status, ExecutionStatus) else self.status
        data["status"] = status_val
        data["summary"]["status"] = status_val

        return data
