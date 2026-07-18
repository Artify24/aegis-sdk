import os
import logging
from typing import Callable
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from packages.context import ExecutionContext
from packages.layers.layer1.base import Layer1Stage
from packages.layers.layer1.exceptions import Layer1ProcessingError

logger = logging.getLogger(__name__)

class CapabilityResult(BaseModel):
    allowed_tools: list[str] = Field(description="The exact names of the tools that are strictly necessary for the request.")
    reason: str = Field(description="Reasoning for why these tools were selected and others were excluded.")

class CapabilityDetectorStage(Layer1Stage):
    """
    Determines the minimum capabilities and tools required for the request.
    Uses the internal Aegis LLM to map the required capabilities to the actual
    available tools registered by the developer.
    """
    def __init__(self, available_tools: list[Callable], model_id: str = "llama-3.3-70b-versatile"):
        self.available_tools = available_tools
        
        aegis_key = os.environ.get("GROQ_API_KEY_AEGIS")
        if not aegis_key:
            raise ValueError("GROQ_API_KEY_AEGIS environment variable must be set.")
            
        self.llm = ChatGroq(
            model=model_id,
            api_key=aegis_key,
            temperature=0.0,
            max_tokens=1024
        ).with_structured_output(CapabilityResult)
        
        self.system_prompt = (
            "You are the Aegis Capability Manager.\n"
            "Your job is to enforce the Principle of Least Privilege.\n"
            "You will be given the user's intent, the required capabilities, and a list of AVAILABLE TOOLS.\n"
            "Return ONLY the names of the tools from the AVAILABLE TOOLS list that are strictly necessary.\n"
            "If no tools are necessary, return an empty list."
        )

    async def process(self, context: ExecutionContext) -> None:
        logger.debug("Layer 1: Running Capability Detection...")
        
        # If there are no tools, nothing to detect
        if not self.available_tools:
            context.layer1.allowed_tools = []
            return
            
        def get_tool_name(t) -> str:
            return getattr(t, "name", getattr(t, "__name__", "unknown"))
            
        def get_tool_desc(t) -> str:
            return getattr(t, "description", getattr(t, "__doc__", "No description"))
            
        tool_descriptions = "\n".join([f"- {get_tool_name(tool)}: {get_tool_desc(tool)}" for tool in self.available_tools])
        
        user_prompt = (
            f"USER PROMPT: {context.request.prompt}\n\n"
            f"DETECTED INTENT: {context.layer1.intent}\n"
            f"REQUIRED CAPABILITIES: {context.layer1.capabilities}\n\n"
            f"AVAILABLE TOOLS:\n{tool_descriptions}"
        )
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            result: CapabilityResult = await self.llm.ainvoke(messages)
            
            # Filter the result to ensure it only contains tools that actually exist
            valid_tool_names = {get_tool_name(t) for t in self.available_tools}
            filtered_tools = [t for t in result.allowed_tools if t in valid_tool_names]
            
            context.layer1.allowed_tools = filtered_tools
            
            logger.debug(f"Layer 1: Capability Detection Complete. Allowed Tools: {filtered_tools}")
            
        except Exception as e:
            logger.error(f"Error during Capability Detection: {e}")
            raise Layer1ProcessingError(f"Failed to detect capabilities: {e}")
