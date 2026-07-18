from typing import Any
from packages.context import ExecutionContext
from packages.runtime.kernel.state import State
from packages.runtime.hooks.base import RuntimeHook
from packages.policy.base import PolicyProvider

class PolicyHook(RuntimeHook):
    """
    Hook that delegates evaluation to a registered PolicyProvider.
    Enforces guardrails on inputs, outputs, and tools.
    """
    def __init__(self, policies: list[PolicyProvider]):
        self.policies = policies

    async def before_execution(self, context: ExecutionContext) -> None:
        pass

    async def before_llm(self, state: State) -> None:
        for policy in self.policies:
            if hasattr(policy, "evaluate_input"):
                await policy.evaluate_input(state)

    async def after_llm(self, state: State, response: Any) -> None:
        for policy in self.policies:
            if hasattr(policy, "evaluate_output"):
                await policy.evaluate_output(response)

    async def before_tool(self, tool_call: dict[str, Any]) -> None:
        for policy in self.policies:
            if hasattr(policy, "evaluate_tool"):
                await policy.evaluate_tool(tool_call)

    async def after_tool(self, tool_result: Any) -> None:
        pass

    async def after_execution(self, context: ExecutionContext, result: Any) -> None:
        pass
