import os
import logging
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from packages.context import ExecutionContext
from packages.layers.layer1.base import Layer1Stage
from packages.layers.layer1.exceptions import Layer1ProcessingError

logger = logging.getLogger(__name__)

class RiskAssessment(BaseModel):
    risk_level: str = Field(description="One of: 'low', 'medium', 'high', 'critical'")
    risk_score: float = Field(description="A score from 0.0 (safest) to 1.0 (most dangerous)")
    risk_factors: list[str] = Field(description="List of detected risk factors, e.g. ['modifies_system_state', 'sensitive_data_access']")
    execution_recommendation: str = Field(description="Recommended execution strategy, e.g. 'execute_normally', 'require_human_approval', 'block'")

class RiskEngineStage(Layer1Stage):
    """
    Performs a final semantic risk assessment using the outputs from all previous Layer 1 stages.
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
        ).with_structured_output(RiskAssessment)
        
        self.system_prompt = (
            "You are the Aegis Risk Assessment Engine.\n"
            "Your job is to evaluate the overall risk of an execution request based on prior analysis.\n"
            "Consider the Intent, Validations, and Capabilities required.\n"
            "Produce a structured risk assessment."
        )

    async def process(self, context: ExecutionContext) -> None:
        logger.debug("Layer 1: Running Risk Assessment Engine...")
        
        l1 = context.layer1
        
        user_prompt = (
            f"USER PROMPT: {context.request.prompt}\n\n"
            f"DETECTED INTENT: {l1.intent} (Category: {l1.task_category})\n"
            f"ALLOWED TOOLS: {l1.allowed_tools}\n"
            f"VALIDATION RESULTS: {l1.validation_result}\n"
        )
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            result: RiskAssessment = await self.llm.ainvoke(messages)
            
            context.layer1.risk_level = result.risk_level
            context.layer1.risk_score = result.risk_score
            context.layer1.risk_factors = result.risk_factors
            context.layer1.execution_recommendation = result.execution_recommendation
            
            logger.debug(f"Layer 1: Risk Engine Complete. Level: {result.risk_level} (Score: {result.risk_score})")
            
        except Exception as e:
            logger.error(f"Error during Risk Assessment: {e}")
            raise Layer1ProcessingError(f"Failed to assess risk: {e}")
