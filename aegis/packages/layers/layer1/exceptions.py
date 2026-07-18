class Layer1ProcessingError(Exception):
    """Base exception for all Layer 1 processing errors."""
    pass

class PromptValidationError(Layer1ProcessingError):
    """Raised when the prompt fails safety, integrity, or injection validation."""
    pass

class MemoryValidationError(Layer1ProcessingError):
    """Raised when the conversation history is poisoned, manipulated, or unsafe."""
    pass
