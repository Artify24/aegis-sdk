from typing import Any, Protocol, runtime_checkable
from packages.context import ExecutionContext
from packages.runtime.kernel.state import State
from packages.models import ExecutionResult

@runtime_checkable
class RuntimeHook(Protocol):
    """
    Interface for hooking into the Aegis runtime lifecycle.
    """
    async def before_execution(self, context: ExecutionContext) -> None:
        """Called before the agent graph starts executing."""
        ...

    async def before_llm(self, state: State) -> None:
        """Called immediately before the LLM is invoked."""
        ...

    async def after_llm(self, state: State, response: Any) -> None:
        """Called immediately after the LLM returns a response."""
        ...

    async def before_tool(self, tool_call: dict[str, Any]) -> None:
        """Called before a tool is executed."""
        ...

    async def after_tool(self, tool_result: Any) -> None:
        """Called after a tool is executed."""
        ...

    async def after_execution(self, context: ExecutionContext, result: ExecutionResult) -> None:
        """Called after the agent graph finishes execution."""
        ...


class HookManager:
    """
    Manages and executes registered runtime hooks.
    """
    def __init__(self):
        self._hooks: list[RuntimeHook] = []

    def register(self, hook: RuntimeHook) -> None:
        """Register a new hook."""
        self._hooks.append(hook)

    async def before_execution(self, context: ExecutionContext) -> None:
        for hook in self._hooks:
            if hasattr(hook, "before_execution"):
                await hook.before_execution(context)

    async def before_llm(self, state: State) -> None:
        for hook in self._hooks:
            if hasattr(hook, "before_llm"):
                await hook.before_llm(state)

    async def after_llm(self, state: State, response: Any) -> None:
        for hook in self._hooks:
            if hasattr(hook, "after_llm"):
                await hook.after_llm(state, response)

    async def before_tool(self, tool_call: dict[str, Any]) -> None:
        for hook in self._hooks:
            if hasattr(hook, "before_tool"):
                await hook.before_tool(tool_call)

    async def after_tool(self, tool_result: Any) -> None:
        for hook in self._hooks:
            if hasattr(hook, "after_tool"):
                await hook.after_tool(tool_result)

    async def after_execution(self, context: ExecutionContext, result: ExecutionResult) -> None:
        for hook in self._hooks:
            if hasattr(hook, "after_execution"):
                await hook.after_execution(context, result)
