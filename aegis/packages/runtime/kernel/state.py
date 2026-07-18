from typing import Annotated, Any
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from packages.models import BehaviorState

class State(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    layer1_context: dict = Field(default_factory=dict)
    behavior_state: BehaviorState | None = None
    tool_telemetry: list[dict] = Field(default_factory=list)