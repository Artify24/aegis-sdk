"""
Aegis SDK — Public Entry Point
================================

This module defines the :class:`Aegis` class, the single public facade
through which developers interact with the Aegis SDK.

**Design principles:**

- *Composition over inheritance* — every subsystem (runtime, providers,
  memory, tools, events, policies, auth) is a swappable slot behind a
  ``Protocol`` interface.
- *Lightweight construction* — ``__init__`` records configuration; heavy
  work is deferred to :meth:`initialize`.
- *Explicit lifecycle* — ``initialize → start → run → shutdown`` with a
  state machine that prevents illegal transitions.
- *Async-first* — lifecycle methods are coroutines because the runtime,
  providers, and networking layers are inherently asynchronous.
- *Context-manager support* — ``async with Aegis(...) as agent:`` guarantees
  cleanup even on unhandled exceptions.

Typical usage::

    from packages.aegis import Aegis

    async def main() -> None:
        agent = (
            Aegis(name="my-agent")
            .with_provider(my_llm_provider)
            .with_memory(my_memory_backend)
            .with_tools([search, calculator])
        )

        async with agent:
            result = await agent.run("Summarise the quarterly report.")
            print(result)
"""

from __future__ import annotations

import enum
import logging
from typing import (
    Any,
    Protocol,
    Self,
    runtime_checkable,
)
from packages.context import ExecutionContext
from packages.models import AgentRequest
import uuid

__all__ = [
    "Aegis",
    "AegisState",
    "AegisError",
    "AegisStateError",
]

logger = logging.getLogger("aegis")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AegisError(Exception):
    """Base exception for all Aegis SDK errors."""


class AegisStateError(AegisError):
    """Raised when a lifecycle method is called in an invalid state."""


# ---------------------------------------------------------------------------
# Lifecycle state machine
# ---------------------------------------------------------------------------


class AegisState(enum.Enum):
    """Represents the current phase of the :class:`Aegis` lifecycle.

    Valid transitions::

        CREATED  ──►  INITIALIZED  ──►  RUNNING  ──►  STOPPED
            │              │               │              │
            └──────────────┴───────────────┴──────► ERRORED
    """

    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERRORED = "errored"


# Legal transitions: mapping from *current* state to set of *allowed* next states.
_TRANSITIONS: dict[AegisState, set[AegisState]] = {
    AegisState.CREATED: {AegisState.INITIALIZED, AegisState.ERRORED},
    AegisState.INITIALIZED: {AegisState.RUNNING, AegisState.STOPPED, AegisState.ERRORED},
    AegisState.RUNNING: {AegisState.STOPPED, AegisState.ERRORED},
    AegisState.STOPPED: set(),
    AegisState.ERRORED: set(),
}


# ---------------------------------------------------------------------------
# Subsystem protocols (minimal contracts)
# ---------------------------------------------------------------------------
# Each protocol captures *only* what Aegis itself needs to call.  Concrete
# implementations live in their own packages and are never imported here.
# ---------------------------------------------------------------------------


@runtime_checkable
class ConfigProvider(Protocol):
    """Provides configuration values to the SDK."""

    def get(self, key: str, default: Any = None) -> Any: ...
    def require(self, key: str) -> Any: ...


@runtime_checkable
class RuntimeProvider(Protocol):
    """Manages the agent runtime loop (kernel + planner + executor)."""

    async def start(self) -> None: ...
    async def execute(self, prompt: str, **kwargs: Any) -> Any: ...
    async def stop(self) -> None: ...


@runtime_checkable
class LLMProvider(Protocol):
    """Abstraction over a large-language-model backend."""

    @property
    def model_id(self) -> str: ...
    async def generate(self, prompt: str, **kwargs: Any) -> Any: ...


@runtime_checkable
class MemoryProvider(Protocol):
    """Long-term / working memory backend."""

    async def store(self, key: str, value: Any) -> None: ...
    async def recall(self, key: str) -> Any | None: ...
    async def clear(self) -> None: ...


@runtime_checkable
class PolicyProvider(Protocol):
    """Evaluates policies / guardrails before and after each action."""

    async def evaluate(self, action: str, context: dict[str, Any]) -> bool: ...


@runtime_checkable
class ToolProvider(Protocol):
    """A single tool that the agent can invoke."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    async def execute(self, **kwargs: Any) -> Any: ...


@runtime_checkable
class EventBus(Protocol):
    """Publish / subscribe mechanism for SDK-internal events."""

    def subscribe(self, event_type: str, handler: Any) -> None: ...
    def unsubscribe(self, event_type: str, handler: Any) -> None: ...
    async def publish(self, event_type: str, payload: Any = None) -> None: ...


@runtime_checkable
class AuthProvider(Protocol):
    """Handles authentication and authorisation for external services."""

    async def authenticate(self) -> bool: ...
    async def get_credentials(self) -> dict[str, str]: ...


# ---------------------------------------------------------------------------
# Aegis — Public SDK entry point
# ---------------------------------------------------------------------------


class Aegis:
    """Public facade and lifecycle manager for the Aegis SDK.

    ``Aegis`` is the **only class** that end-users need to import.  It
    composes every subsystem through Protocol-typed slots so that
    implementations remain swappable and independently testable.

    Parameters
    ----------
    name:
        A human-readable identifier for this agent instance.
    version:
        Semantic version string surfaced in logs and telemetry.
    config:
        An optional :class:`ConfigProvider` instance.  When ``None``, a
        default in-memory configuration is created during
        :meth:`initialize`.
    metadata:
        Arbitrary key/value pairs attached to the instance (useful for
        tracing, tagging, or multi-tenant routing).

    Example
    -------
    ::

        agent = (
            Aegis(name="analyst")
            .with_provider(OpenAIProvider(model="gpt-4o"))
            .with_tools([web_search, calculator])
        )

        async with agent:
            answer = await agent.run("What is 42 * 17?")
    """

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        name: str = "aegis",
        *,
        version: str = "0.1.0",
        config: ConfigProvider | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # Identity
        self._name: str = name
        self._version: str = version
        self._metadata: dict[str, Any] = metadata or {}

        # Lifecycle
        self._state: AegisState = AegisState.CREATED

        # Subsystem slots — all optional until initialize()
        self._config: ConfigProvider | None = config
        self._runtime: RuntimeProvider | None = None
        self._provider: LLMProvider | None = None
        self._memory: MemoryProvider | None = None
        self._policies: list[PolicyProvider] = []
        self._tools: list[ToolProvider] = []
        self._event_bus: EventBus | None = None
        self._auth: AuthProvider | None = None
        self._system_prompt: str | None = None
        self._execution_store: Any | None = None

        logger.debug("Aegis instance '%s' created (v%s).", name, version)

    # ------------------------------------------------------------------ #
    # Read-only properties
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        """Human-readable instance name."""
        return self._name

    @property
    def version(self) -> str:
        """SDK / instance version string."""
        return self._version

    @property
    def state(self) -> AegisState:
        """Current lifecycle state (read-only)."""
        return self._state

    @property
    def metadata(self) -> dict[str, Any]:
        """Arbitrary metadata attached to this instance."""
        return self._metadata

    @property
    def is_running(self) -> bool:
        """``True`` when the agent loop is active."""
        return self._state is AegisState.RUNNING

    # ------------------------------------------------------------------ #
    # Builder-style registration (fluent API)
    # ------------------------------------------------------------------ #

    def with_config(self, config: ConfigProvider) -> Self:
        """Attach a :class:`ConfigProvider` implementation.

        Must be called **before** :meth:`initialize`.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_config")
        self._config = config
        logger.debug("Config provider registered.")
        return self

    def with_provider(self, provider: LLMProvider) -> Self:
        """Attach the primary LLM provider.

        Parameters
        ----------
        provider:
            Any object satisfying the :class:`LLMProvider` protocol.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_provider")
        self._provider = provider
        logger.debug("LLM provider registered: %s", getattr(provider, "model_id", "unknown"))
        return self

    def with_runtime(self, runtime: RuntimeProvider) -> Self:
        """Attach a custom :class:`RuntimeProvider`.

        When omitted, :meth:`initialize` will construct the default
        runtime from ``packages.control.runtime``.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_runtime")
        self._runtime = runtime
        logger.debug("Runtime provider registered.")
        return self

    def with_memory(self, memory: MemoryProvider) -> Self:
        """Attach a :class:`MemoryProvider` backend.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_memory")
        self._memory = memory
        logger.debug("Memory provider registered.")
        return self

    def with_system_prompt(self, prompt: str) -> Self:
        """Override the default system prompt sent to the LLM on every request.

        Use this to define the agent's identity, persona, and behavioral rules
        in a way that is specific to your application domain.  The SDK ships
        with a sensible default; this method lets you replace it entirely.

        Parameters
        ----------
        prompt:
            The full system prompt string.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_system_prompt")
        self._system_prompt = prompt
        logger.debug("Custom system prompt registered (%d chars).", len(prompt))
        return self

    def with_policy(self, policy: PolicyProvider | str | list[PolicyProvider | str]) -> Self:
        """Register a guardrail / policy evaluator.

        Multiple policies can be registered; they are evaluated **in
        registration order**.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_policy")
        
        # Separate string policies from custom PolicyProviders
        str_policies = []
        custom_policies = []
        
        policy_list = policy if isinstance(policy, list) else [policy]
        
        for p in policy_list:
            if isinstance(p, str):
                str_policies.append(p)
            else:
                custom_policies.append(p)
                
        # Register custom policies
        self._policies.extend(custom_policies)
        
        # Bundle all string policies into a single NaturalLanguagePolicy to save LLM calls
        if str_policies:
            from packages.policy.nl_policy import NaturalLanguagePolicy
            combined_rules = "\n".join([f"- {rule}" for rule in str_policies])
            self._policies.append(NaturalLanguagePolicy(rule=combined_rules))

        logger.debug("Policy registered (total: %d).", len(self._policies))
        return self

    def with_tools(self, tools: list[ToolProvider]) -> Self:
        """Register one or more tools that the agent may invoke.

        Calling this method multiple times **appends** to the tool list.

        Parameters
        ----------
        tools:
            A list of objects satisfying the :class:`ToolProvider`
            protocol.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_tools")
        self._tools.extend(tools)
        logger.debug("Tools registered (total: %d).", len(self._tools))
        return self

    def with_event_bus(self, event_bus: EventBus) -> Self:
        """Attach an :class:`EventBus` implementation.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_event_bus")
        self._event_bus = event_bus
        logger.debug("Event bus registered.")
        return self

    def with_auth(self, auth: AuthProvider) -> Self:
        """Attach an :class:`AuthProvider` implementation.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_auth")
        self._auth = auth
        logger.debug("Auth provider registered.")
        return self

    def with_execution_store(self, store: Any) -> Self:
        """Attach an ExecutionStore implementation for observability.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for method chaining.
        """
        self._assert_state(AegisState.CREATED, "with_execution_store")
        self._execution_store = store
        logger.debug("Execution store registered.")
        return self

    # ------------------------------------------------------------------ #
    # Lifecycle methods
    # ------------------------------------------------------------------ #

    async def initialize(self) -> Self:
        """Prepare all subsystems without starting the agent loop.

        This method:

        1. Validates that required subsystems are registered.
        2. Creates defaults for any optional subsystem not yet provided.
        3. Wires subsystems together (dependency injection).
        4. Transitions state to :attr:`AegisState.INITIALIZED`.

        Raises
        ------
        AegisStateError
            If called from any state other than ``CREATED``.
        AegisError
            If a required subsystem is missing.

        Returns
        -------
        Self
            The same ``Aegis`` instance, for chaining.
        """
        self._assert_state(AegisState.CREATED, "initialize")

        try:
            # --- Step 1: validate required subsystems --------------------
            # TODO: Determine which subsystems are strictly required vs.
            #       optional.  For now we only warn when no LLM provider
            #       is attached.
            if self._provider is None:
                logger.warning(
                    "No LLM provider registered — the agent will not be "
                    "able to generate responses until one is attached."
                )

            # --- Step 2: create defaults for optional subsystems ---------
            # TODO: Instantiate default ConfigProvider from
            #       packages.config when self._config is None.
            # TODO: Instantiate default EventBus from
            #       packages.control.events when self._event_bus is None.
            
            if self._execution_store is None:
                from packages.observability.store import JsonExecutionStore
                self._execution_store = JsonExecutionStore()

            # --- Step 3: wire subsystems together ------------------------
            from packages.runtime.factory import RuntimeFactory
            self._runtime = RuntimeFactory.build(
                provider=self._provider,
                tools=self._tools,
                policies=self._policies,
                memory=self._memory,
                system_prompt=self._system_prompt,
                execution_store=self._execution_store
            )

            self._transition_to(AegisState.INITIALIZED)
            logger.info("Aegis '%s' initialized.", self._name)

        except Exception as exc:
            self._transition_to(AegisState.ERRORED)
            raise AegisError(f"Initialization failed: {exc}") from exc

        return self

    async def start(self) -> Self:
        """Start the agent runtime loop.

        The agent transitions to :attr:`AegisState.RUNNING` and begins
        accepting work via :meth:`run`.

        Raises
        ------
        AegisStateError
            If called from any state other than ``INITIALIZED``.
        """
        self._assert_state(AegisState.INITIALIZED, "start")

        try:
            if hasattr(self._runtime, "initialize"):
                await self._runtime.initialize()
            
            # TODO: Publish "aegis.started" event via self._event_bus.

            self._transition_to(AegisState.RUNNING)
            logger.info("Aegis '%s' is now running.", self._name)

        except Exception as exc:
            self._transition_to(AegisState.ERRORED)
            raise AegisError(f"Start failed: {exc}") from exc

        return self

    async def run(self, prompt: str, **kwargs: Any) -> Any:
        """Submit a prompt to the agent and return the result.

        This is the primary method that SDK consumers call after the
        agent has been started.

        Parameters
        ----------
        prompt:
            The natural-language instruction or query.
        **kwargs:
            Additional execution parameters forwarded to the runtime
            (e.g. ``temperature``, ``max_tokens``, ``stream``).

        Returns
        -------
        Any
            The structured result from the runtime execution pipeline.

        Raises
        ------
        AegisStateError
            If the agent is not in ``RUNNING`` state.
        NotImplementedError
            Until the runtime pipeline is implemented.
        """
        self._assert_state(AegisState.RUNNING, "run")

        # Create execution context
        import time
        execution_id = kwargs.get('execution_id', str(uuid.uuid4()))
        correlation_id = kwargs.get('correlation_id', str(uuid.uuid4()))
        request = AgentRequest(prompt=prompt, stream=kwargs.get('stream', False))
        
        context = ExecutionContext(
            request=request, 
            execution_id=execution_id,
            correlation_id=correlation_id,
            started_at=time.time(),
            sdk_version=self._version,
            runtime_version="1.0.0",
            project_name=kwargs.get('project_name', 'aegis-default'),
            environment=kwargs.get('environment', 'development')
        )
        
        # Execute the runtime
        result = await self._runtime.execute(context)
        
        # TODO: Publish "aegis.run.completed" event.
        return result

    async def shutdown(self) -> None:
        """Gracefully stop the agent and release all resources.

        Safe to call from any non-terminal state.  After shutdown the
        instance cannot be restarted.

        Raises
        ------
        AegisStateError
            If already ``STOPPED`` or ``ERRORED``.
        """
        if self._state in {AegisState.STOPPED, AegisState.ERRORED}:
            logger.debug("Aegis '%s' already in terminal state %s.", self._name, self._state.value)
            return

        try:
            if hasattr(self._runtime, "shutdown"):
                await self._runtime.shutdown()
            
            # TODO: Flush / close memory provider.
            # TODO: Publish "aegis.shutdown" event, then close event bus.
            # TODO: Revoke auth credentials if applicable.

            self._transition_to(AegisState.STOPPED)
            logger.info("Aegis '%s' shut down.", self._name)

        except Exception as exc:
            self._transition_to(AegisState.ERRORED)
            raise AegisError(f"Shutdown failed: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Async context manager
    # ------------------------------------------------------------------ #

    async def __aenter__(self) -> Self:
        """Enter the async context: initialize and start the agent.

        Usage::

            async with Aegis(name="a") as agent:
                await agent.run("Hello")
        """
        if self._state is AegisState.CREATED:
            await self.initialize()
        if self._state is AegisState.INITIALIZED:
            await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """Exit the async context: always call :meth:`shutdown`."""
        await self.shutdown()
        # Do not suppress exceptions.
        return False

    # ------------------------------------------------------------------ #
    # Introspection helpers
    # ------------------------------------------------------------------ #

    def get_registered_tools(self) -> list[str]:
        """Return the names of all registered tools."""
        return [t.name for t in self._tools]

    def get_registered_policies(self) -> int:
        """Return the count of registered policies."""
        return len(self._policies)

    def has_provider(self) -> bool:
        """Check whether an LLM provider has been attached."""
        return self._provider is not None

    def has_memory(self) -> bool:
        """Check whether a memory backend has been attached."""
        return self._memory is not None

    # ------------------------------------------------------------------ #
    # State-machine helpers (private)
    # ------------------------------------------------------------------ #

    def _assert_state(self, expected: AegisState, method_name: str) -> None:
        """Raise :class:`AegisStateError` if the current state is wrong."""
        if self._state is not expected:
            raise AegisStateError(
                f"Cannot call '{method_name}()' in state "
                f"'{self._state.value}'; expected '{expected.value}'."
            )

    def _transition_to(self, target: AegisState) -> None:
        """Attempt a state transition, raising on illegal moves."""
        allowed = _TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise AegisStateError(
                f"Illegal state transition: "
                f"'{self._state.value}' → '{target.value}'."
            )
        previous = self._state
        self._state = target
        logger.debug(
            "State transition: %s → %s",
            previous.value,
            target.value,
        )

    # ------------------------------------------------------------------ #
    # Dunder helpers
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"Aegis(name={self._name!r}, version={self._version!r}, "
            f"state={self._state.value!r})"
        )

    def __str__(self) -> str:
        return f"<Aegis '{self._name}' [{self._state.value}]>"
