from packages.runtime.kernel.state import State
from langchain_core.language_models.chat_models import BaseChatModel
from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.events.models import PlannerStepStarted, PlannerStepFinished
from packages.runtime.hooks.base import HookManager

from packages.policy.base import PolicyViolationError, ApprovalRequiredError
from langchain_core.messages import AIMessage
import asyncio
import logging

logger = logging.getLogger(__name__)
class PlannerNode:
    """
    The Planner node wraps the LLM invocation.
    It takes the current State, calls the LLM (which has tools bound to it),
    and returns the LLM's response to be appended to the state.
    """
    def __init__(
        self, 
        llm: BaseChatModel, 
        event_bus: RuntimeEventBus = None,
        hook_manager: HookManager = None,
        fallback_llm: BaseChatModel = None,
        timeout_seconds: int = 30,
        system_prompt: str = None
    ):
        self.llm = llm
        self.event_bus = event_bus
        self.hook_manager = hook_manager
        self.fallback_llm = fallback_llm
        self.timeout_seconds = timeout_seconds
        self.system_prompt = system_prompt

    async def __call__(self, state: State):
        try:
            if self.hook_manager:
                await self.hook_manager.before_llm(state)
            
            if self.event_bus:
                await self.event_bus.publish(PlannerStepStarted())

            # Prepend system prompt if provided
            messages_to_send = state.messages
            if self.system_prompt:
                from langchain_core.messages import SystemMessage
                messages_to_send = [SystemMessage(content=self.system_prompt)] + messages_to_send

            # 2. Call the LLM with timeout and fallback
            try:
                response = await asyncio.wait_for(
                    self.llm.ainvoke(messages_to_send), 
                    timeout=self.timeout_seconds
                )
            except Exception as e:
                logger.warning(f"Primary LLM failed or timed out: {e}. Attempting fallback.")
                if self.fallback_llm:
                    response = await asyncio.wait_for(
                        self.fallback_llm.ainvoke(state.messages),
                        timeout=self.timeout_seconds
                    )
                else:
                    raise RuntimeError(f"Primary LLM failed and no fallback configured: {e}")

            if self.hook_manager:
                await self.hook_manager.after_llm(state, response)

            if self.event_bus:
                # We can't easily parse reasoning without a structured output, but we can emit the event
                await self.event_bus.publish(PlannerStepFinished(decision="Decided next step", reasoning="Based on tools"))

            return {"messages": [response]}
        except ApprovalRequiredError as e:
            error_message = AIMessage(content=f"⚠️ **Action Requires Approval**: {e.message}\n\nType 'I approve' to proceed.")
            return {"messages": [error_message]}
        except PolicyViolationError as e:
            # Elegant error handling: short-circuit and return the violation message
            error_message = AIMessage(content=f"Request blocked by policy: {e.message}")
            return {"messages": [error_message]}
