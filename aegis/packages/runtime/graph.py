from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.language_models.chat_models import BaseChatModel

from packages.runtime.kernel.state import State
from packages.runtime.nodes.planner import PlannerNode
from packages.runtime.nodes.executor import ExecutorNode

from packages.runtime.events.bus import RuntimeEventBus
from packages.runtime.hooks.base import HookManager

def build_agent_graph(
    llm: BaseChatModel, 
    tools: list, 
    memory: BaseCheckpointSaver,
    event_bus: RuntimeEventBus = None,
    hook_manager: HookManager = None,
    fallback_llm: BaseChatModel = None,
    timeout_seconds: int = 30
) -> CompiledStateGraph:
    """
    Constructs and returns the compiled LangGraph StateGraph for the agent.
    """
    workflow = StateGraph(State)

    # 1. Define and add the Planner Node
    planner_node = PlannerNode(llm, event_bus, hook_manager, fallback_llm, timeout_seconds)
    workflow.add_node("planner", planner_node)
    
    # 2. Define and add the Executor (Tool) Node if tools are provided
    if tools:
        executor_node = ExecutorNode(tools, event_bus, hook_manager, timeout_seconds)
        workflow.add_node("executor", executor_node)
        
        # Wire conditional edges from planner to executor/END
        workflow.add_conditional_edges(
            "planner",
            tools_condition,
            {"tools": "executor", "__end__": END}
        )
        # Wire edge from executor back to planner
        workflow.add_edge("executor", "planner")
    else:
        # No tools, just a direct edge from planner to END
        workflow.add_edge("planner", END)

    # 3. Wire dependencies (Set entry point)
    workflow.add_edge(START, "planner")

    # Compile the graph with the checkpointer (memory)
    return workflow.compile(checkpointer=memory)
