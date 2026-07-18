from typing import Any, Dict, Optional
from packages.models import MemorySource

class MemoryPolicyException(Exception):
    """Raised when a memory operation violates an established policy."""
    pass

class MemoryPolicyEvaluator:
    """
    Evaluates rules before a memory operation is permitted.
    Ensures memory sources designated as Read-Only, Sensitive, or Ephemeral 
    are strictly governed. Future integration with Layer 1 will pass execution context here.
    """
    
    @staticmethod
    def evaluate_write(source: MemorySource, key: str, value: Any, context: Optional[Dict[str, Any]] = None) -> None:
        """Evaluates whether a write operation is allowed."""
        if source.metadata.get("read_only", False):
            raise MemoryPolicyException(f"Memory source '{source.name}' is designated as Read-Only.")

        # If it's a private scope, check if the context matches the owner (stub rule)
        if source.scope == "private":
            owner = source.metadata.get("owner_id")
            requester = context.get("user_id") if context else None
            if owner and owner != requester:
                raise MemoryPolicyException(f"Write access denied to private memory source '{source.name}'.")

    @staticmethod
    def evaluate_read(source: MemorySource, key: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Evaluates whether a read operation is allowed."""
        if source.metadata.get("sensitive", False):
            clearance = context.get("clearance_level", "low") if context else "low"
            required_clearance = source.metadata.get("required_clearance", "high")
            if clearance != required_clearance:
                raise MemoryPolicyException(f"Read access denied to sensitive memory source '{source.name}'. Clearance '{clearance}' does not meet required '{required_clearance}'.")
                
        # Private scope checks
        if source.scope == "private":
            owner = source.metadata.get("owner_id")
            requester = context.get("user_id") if context else None
            if owner and owner != requester:
                raise MemoryPolicyException(f"Read access denied to private memory source '{source.name}'.")
