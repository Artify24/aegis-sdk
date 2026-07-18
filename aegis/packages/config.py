from typing import Any
from dataclasses import dataclass, field


@dataclass(slots=True)
class AegisConfig:
    """Configuration for an Aegis agent."""
    model: str
    temperature: float = 0.5 
    memory:bool = False
    tools:list[Any] = field(default_factory=list)
    max_tokens: int | None = None
    stream: bool = False
    fallback_model: str | None = None
    timeout_seconds: int = 120
    system_prompt: str | None = None
    
    

