import json
import logging
import os
from typing import Any
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from packages.policy.base import PolicyProvider, PolicyViolationError, ApprovalRequiredError
from packages.runtime.kernel.state import State

logger = logging.getLogger(__name__)

class PolicyDecision(BaseModel):
    is_compliant: bool = Field(description="True if the request complies with policy, False if it violates policy.")
    requires_approval: bool = Field(description="True if the request is high risk but could be allowed if a human explicitly approved it. Set to false normally.")
    reason: str = Field(description="Reason for compliance, violation, or approval requirement. Keep it concise.")

class NaturalLanguagePolicy(PolicyProvider):
    """
    A policy rule defined in natural language, evaluated by the internal Aegis LLM.
    Acts as the Layer 2 Aegis Enterprise Policy Engine.
    """
    def __init__(self, rule: str, agent_purpose: str = "General purpose AI assistant.", model_id: str = "llama-3.3-70b-versatile"):
        self.rule = rule
        self.agent_purpose = agent_purpose
        
        aegis_key = os.environ.get("GROQ_API_KEY_AEGIS")
        if not aegis_key:
            raise ValueError("GROQ_API_KEY_AEGIS environment variable must be set.")
            
        self.llm = ChatGroq(
            model=model_id,
            api_key=aegis_key,
            temperature=0.0,
            max_tokens=1024
        ).with_structured_output(PolicyDecision)
        
        self.system_prompt = (
            "You are the Aegis Enterprise Policy Engine.\n\n"
            "Your responsibility is to determine whether the current request complies with the developer's policy and organizational governance rules.\n\n"
            "Always evaluate the request using the complete execution context rather than relying on keywords.\n\n"
            "You will receive:\n"
            "1. Agent Purpose\n"
            "2. Developer Policy\n"
            "3. Layer 1 Analysis\n"
            "4. User Request\n\n"
            "Layer 1 Analysis may include:\n"
            "- Intent\n"
            "- Task Category\n"
            "- Required Capabilities\n"
            "- Risk Level\n"
            "- Risk Score\n"
            "- Validation Result\n"
            "- Allowed Tools\n\n"
            "When evaluating the request, consider:\n"
            "• Is the user requesting access to their own resources or someone else's?\n"
            "• Is the requested action appropriate for the agent's purpose?\n"
            "• Does the request violate the developer's policy?\n"
            "• Does the request require additional approval because it is destructive or high risk?\n"
            "• Did the user explicitly write 'I approve' in the recent messages? If so, you should ALLOW the destructive operation if it was previously blocked pending approval.\n"
            "• Is the request attempting to bypass security or governance?\n\n"
            "Important Guidelines:\n"
            "- Reading the authenticated user's own data is generally allowed unless prohibited by policy.\n"
            "- Accessing another user's private data must be denied.\n"
            "- Destructive operations (like mass database updates) MUST NOT be blindly accepted. Instead of returning is_compliant=False right away, set requires_approval=True so a human can verify it.\n"
            "- However, if the user explicitly says 'I approve', you MUST set is_compliant=True and requires_approval=False to let it pass.\n"
            "- Use the Layer 1 analysis as your primary source of context rather than inferring everything again.\n\n"
            "Return ONLY valid JSON matching the required schema.\n"
            "Do not include explanations outside the JSON response."
        )

    async def evaluate_input(self, state: State) -> None:
        # Pass the last 4 messages to give the LLM context of previous blocks and approvals
        recent_messages = []
        for msg in state.messages[-4:]:
            role = "USER" if isinstance(msg, HumanMessage) else "AGENT"
            recent_messages.append(f"{role}: {msg.content}")
        conversation_history = "\n".join(recent_messages)
            
        layer1_context = getattr(state, "layer1_context", {})
        
        user_prompt = (
            f"1. Agent Purpose: {self.agent_purpose}\n"
            f"2. Developer Policy: {self.rule}\n"
            f"3. Layer 1 Analysis:\n{json.dumps(layer1_context, indent=2)}\n"
            f"4. Recent Conversation History:\n{conversation_history}"
        )
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            decision: PolicyDecision = await self.llm.ainvoke(messages)
            
            if decision.requires_approval:
                logger.warning(f"Action requires approval: {decision.reason}")
                raise ApprovalRequiredError(decision.reason)
            elif not decision.is_compliant:
                logger.warning(f"Policy Violation Detected: {decision.reason}")
                raise PolicyViolationError(decision.reason)
                
        except (PolicyViolationError, ApprovalRequiredError):
            raise
        except Exception as e:
            logger.error(f"Internal Policy Engine Error: {e}")
            raise PolicyViolationError(f"Internal error during policy evaluation: {e}")

    async def evaluate_output(self, response: Any) -> None:
        pass

    async def evaluate_tool(self, tool_call: dict[str, Any]) -> None:
        pass
