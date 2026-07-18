import logging
from typing import Sequence
from packages.models import ProposedAction, GovernanceResult
from packages.context import ExecutionContext
from packages.policy.base import PolicyViolationError
from .validators import (
    IdentityValidator,
    PermissionValidator,
    ToolAuthorizationValidator,
)

logger = logging.getLogger(__name__)

class GovernanceEngine:
    """
    Layer 2: Execution Governance.
    Acts as the strict trust boundary between the Untrusted Planner and the Execution Engine.
    """
    def __init__(self):
        # Initialize default validators
        self.validators = [
            IdentityValidator(),
            PermissionValidator(),
            ToolAuthorizationValidator(),
        ]
        
    async def evaluate(self, action: ProposedAction, context: ExecutionContext) -> GovernanceResult:
        """
        Evaluate a proposed action against all validators.
        """
        logger.info(f"Layer 2: Evaluating proposed action: {action.tool_name}")
        
        for validator in self.validators:
            validator_name = validator.__class__.__name__
            try:
                # Every validator raises a PolicyViolationError if it fails
                await validator.validate(action, context)
            except PolicyViolationError as e:
                logger.warning(f"Layer 2 Blocked Action! Validator: {validator_name}, Reason: {e.message}")
                
                # Create an audit event for the failure
                audit_event = {
                    "event": "governance_block",
                    "action": action.tool_name,
                    "failed_validator": validator_name,
                    "reason": e.message
                }
                
                return GovernanceResult(
                    approved=False,
                    approved_action=None,
                    failed_validator=validator_name,
                    failure_reason=e.message,
                    audit_event=audit_event
                )
            except Exception as e:
                # Unhandled exception in validator
                logger.error(f"Validator {validator_name} crashed: {e}")
                return GovernanceResult(
                    approved=False,
                    approved_action=None,
                    failed_validator=validator_name,
                    failure_reason=f"Internal validator error: {e}"
                )
                
        # If all validators pass
        logger.info(f"Layer 2: Action Approved: {action.tool_name}")
        
        # Constraints generation could happen here or in a separate validator that augments the action
        constraints = {
            "timeout_seconds": 30 # Stub constraint
        }
        
        audit_event = {
            "event": "governance_approve",
            "action": action.tool_name
        }
        
        return GovernanceResult(
            approved=True,
            approved_action=action, # Handing the action down as approved
            constraints=constraints,
            audit_event=audit_event
        )
