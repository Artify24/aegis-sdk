from typing import Sequence, Optional
from packages.config import AegisConfig
from packages.runtime.kernel.kernel import RuntimeKernel
from packages.runtime.hooks.policy import PolicyHook
from packages.policy.base import PolicyProvider
from packages.aegis import LLMProvider, ToolProvider, MemoryProvider
from typing import Any

class RuntimeFactory:
    """
    Translates the public builder API into internal runtime objects.
    """
    @staticmethod
    def build(
        provider: LLMProvider,
        tools: Sequence[ToolProvider],
        policies: Sequence[PolicyProvider],
        memory: Optional[MemoryProvider] = None,
        system_prompt: Optional[str] = None,
        execution_store: Optional[Any] = None
    ) -> RuntimeKernel:
        # 1. Build the AegisConfig from the provided builder inputs
        model_id = getattr(provider, "model_id", "llama3-8b-8192")
        
        config = AegisConfig(
            model=model_id,
            tools=list(tools),
            system_prompt=system_prompt
        )
        
        # 2. Instantiate the Runtime Kernel
        kernel = RuntimeKernel(config=config, memory=memory, execution_store=execution_store)
        
        # 3. Register Policies as Hooks
        if policies:
            policy_hook = PolicyHook(policies=list(policies))
            kernel.hook_manager.register(policy_hook)
            
        return kernel
