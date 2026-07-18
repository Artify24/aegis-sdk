import os
import logging
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from packages.context import ExecutionContext
from packages.layers.layer1.base import Layer1Stage
from packages.layers.layer1.exceptions import Layer1ProcessingError

logger = logging.getLogger(__name__)

class IntentResult(BaseModel):
    primary_intent: str = Field(description="The primary intent of the user (e.g. 'email_read', 'weather_query', 'database_query').")
    user_goal: str = Field(description="A short summary of what the user is trying to achieve.")
    task_category: str = Field(description="The broad category of the task (e.g. 'information_retrieval', 'action_execution', 'analysis').")
    required_capabilities: list[str] = Field(description="A list of generic capabilities needed (e.g. ['email.read', 'weather.read']).")
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0.")

class IntentAnalysisStage(Layer1Stage):
    """
    Uses the internal Aegis LLM to understand the user's request.
    Extracts Primary Intent, User Goal, Task Category, Required Capabilities, and Confidence Score.
    """
    def __init__(self, model_id: str = "llama-3.3-70b-versatile"):
        aegis_key = os.environ.get("GROQ_API_KEY_AEGIS")
        if not aegis_key:
            raise ValueError("GROQ_API_KEY_AEGIS environment variable must be set.")
            
        self.llm = ChatGroq(
            model=model_id,
            api_key=aegis_key,
            temperature=0.0,
            max_tokens=1024
        ).with_structured_output(IntentResult)
        
        self.system_prompt = (
            "You are the Aegis Intent Analysis Engine.\n"
            "Your job is to understand the user's true intent and determine what capabilities they need.\n"
            "Output the primary intent, their high-level goal, the broad task category, and the required capabilities.\n"
            "Be precise and structured."
        )

    async def process(self, context: ExecutionContext) -> None:
        user_prompt = context.request.prompt
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"USER PROMPT:\n{user_prompt}")
        ]
        
        logger.debug("Layer 1: Running Intent Analysis...")
        try:
            result: IntentResult = await self.llm.ainvoke(messages)
            
            # Update Layer 1 Context
            context.layer1.intent = result.primary_intent
            context.layer1.task_category = result.task_category
            context.layer1.capabilities = result.required_capabilities
            context.layer1.confidence_score = result.confidence_score
            
            logger.debug(f"Layer 1: Intent Analysis Complete. Intent: {result.primary_intent} (Confidence: {result.confidence_score})")
            
        except Exception as e:
            logger.error(f"Error during Intent Analysis: {e}")
            raise Layer1ProcessingError(f"Failed to analyze intent: {e}")
