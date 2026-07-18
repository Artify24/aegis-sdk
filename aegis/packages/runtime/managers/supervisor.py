import logging
import os
import re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.events.models import PlannerStepFinished
from packages.context import ExecutionContext

logger = logging.getLogger(__name__)

class ExecutionSupervisor:
    """
    Continuously supervises runtime decisions.
    Explains WHY the runtime performed each step by recording Planner Reasoning and Decisions.
    Subscribes to Planner events.
    """
    def __init__(self, event_bus: RuntimeEventBus, context: ExecutionContext, model_id: str = "llama-3.1-8b-instant"):
        self.event_bus = event_bus
        self.context = context
        
        aegis_key = os.environ.get("GROQ_API_KEY_AEGIS")
        if aegis_key:
            self.llm = ChatGroq(model=model_id, api_key=aegis_key, temperature=0.0, max_tokens=200)
        else:
            self.llm = None
            
        self.event_bus.subscribe(PlannerStepFinished, self._supervise_planner_step)
        
    async def _supervise_planner_step(self, event: PlannerStepFinished) -> None:
        """Analyze and record the semantic reason for a planner's decision."""
        if not self.llm:
            return
            
        # We use a lightweight LLM call to generate a supervisor summary of the step
        # This is strictly observational, not blocking.
        system_prompt = (
            "You are the Execution Supervisor. "
            "Explain in one concise sentence WHY the runtime planner made the following decision, "
            "given the original Layer 1 Intent."
        )
        human_prompt = (
            f"Original Intent: {self.context.layer1.intent}\n"
            f"Planner Decision: {event.decision}\n"
            f"Planner Reasoning: {event.reasoning}\n"
        )
        
        try:
            response = await self.llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
            
            # Clean up deep reasoning tags if the model produces them
            clean_content = re.sub(r'<think>.*?</think>', '', response.content, flags=re.DOTALL).strip()
            
            event.metadata["supervisor_explanation"] = clean_content
            logger.info(f"[Supervisor] Explained Decision: {clean_content}")
        except Exception as e:
            logger.warning(f"[Supervisor] Failed to supervise step: {e}")

    def cleanup(self) -> None:
        """Unsubscribe from the event bus to prevent memory leaks."""
        self.event_bus.unsubscribe(PlannerStepFinished, self._supervise_planner_step)
