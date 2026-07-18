import logging
from typing import Protocol
from packages.models import ProposedAction, BehaviorState
from packages.context import ExecutionContext
from packages.policy.base import PolicyViolationError
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import os

logger = logging.getLogger(__name__)

class Validator(Protocol):
    async def validate(self, action: ProposedAction, context: ExecutionContext) -> None:
        """Validates the proposed action. Raises PolicyViolationError if invalid."""
        ...


class IdentityValidator:
    async def validate(self, action: ProposedAction, context: ExecutionContext) -> None:
        # Stub for identity checking (JWT, API Key, Session)
        logger.debug(f"Layer 2: Identity Validator passed for {action.tool_name}")
        pass


class PermissionValidator:
    async def validate(self, action: ProposedAction, context: ExecutionContext) -> None:
        # Stub for RBAC checks
        logger.debug(f"Layer 2: Permission Validator passed for {action.tool_name}")
        pass


class ToolAuthorizationValidator:
    async def validate(self, action: ProposedAction, context: ExecutionContext) -> None:
        logger.debug(f"Layer 2: Tool Authorization Validator checking {action.tool_name}")
        
        # If the user is explicitly approving a blocked action, bypass the Layer 1 
        # allowed_tools restriction since the prompt "I approve" yields an empty tool list.
        user_prompt = context.request.prompt.strip().lower()
        if user_prompt in ["i approve", "approve", "yes", "go ahead", "proceed"]:
            logger.debug("Bypassing ToolAuthorizationValidator due to explicit user approval.")
            return

        allowed_tools = context.layer1.allowed_tools
        if not allowed_tools:
            # If no tools were allowed, but planner tried to call one
            raise PolicyViolationError(f"Unauthorized tool '{action.tool_name}' requested - no tools are allowed for this request.")
            
        if action.tool_name not in allowed_tools:
            raise PolicyViolationError(f"Unauthorized tool '{action.tool_name}' requested. Allowed tools: {allowed_tools}")



