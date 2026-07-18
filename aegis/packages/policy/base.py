from typing import Any, Protocol, runtime_checkable

class PolicyViolationError(Exception):
    """
    Raised when an input, output, or tool action violates a registered policy.
    The runtime intercepts this to gracefully fail.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ApprovalRequiredError(PolicyViolationError):
    """
    Raised when an action is high-risk but permissible if the user explicitly approves.
    """
    pass

@runtime_checkable
class PolicyProvider(Protocol):
    """
    Interface for implementing guardrails and policies.
    """
    async def evaluate_input(self, state: dict[str, Any]) -> None:
        """Evaluate input before LLM execution. Raise PolicyViolationError if failed."""
        ...

    async def evaluate_output(self, response: Any) -> None:
        """Evaluate output after LLM execution. Raise PolicyViolationError if failed."""
        ...

    async def evaluate_tool(self, tool_call: dict[str, Any]) -> None:
        """Evaluate a tool call before execution. Raise PolicyViolationError if failed."""
        ...
