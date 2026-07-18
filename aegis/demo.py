import streamlit as st
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from packages.aegis import Aegis
from demotools.provider import GroqProvider
from demotools.tools import (
    github_read_repos, github_read_issues, github_read_prs, github_create_issue, github_search_commits,
    email_read_inbox, email_send, email_reply,
    db_query, db_insert, db_update, db_backup_table, db_restore_table
)

# Layer 4 Imports
from packages.models import MemorySource
from packages.memory.registry import MemoryRegistry
from packages.memory.adapters.langgraph_adapter import LangGraphMemoryAdapter
from packages.memory.manager import MemoryManager
from packages.memory.semantic import SemanticMemory
from packages.memory.retrieval import KnowledgeRetrieval
from packages.observability.store import AegisCloudExecutionStore
from langchain_core.tools import tool

st.set_page_config(page_title="Aegis Cloud Support", page_icon="🛡️", layout="wide")

st.title("🛡️ Aegis Cloud Customer Support")
st.markdown("A working prototype of the Aegis SDK Agentic Support System with full Layer Governance.")

# --- Initialization (Cached) ---
@st.cache_resource
def init_memory():
    registry = MemoryRegistry()
    adapter = LangGraphMemoryAdapter()
    registry.register_provider("default_memory", adapter)
    
    registry.register_source(MemorySource(
        name="knowledge_base", provider_name="default_memory", namespace="semantic_docs", scope="global", semantic=True
    ))
    registry.register_source(MemorySource(
        name="secure_vault", provider_name="default_memory", namespace="vault", scope="global", metadata={"read_only": True}
    ))
    
    manager = MemoryManager(registry)
    retrieval = KnowledgeRetrieval(SemanticMemory(manager, "knowledge_base"))
    return adapter, manager, retrieval

adapter, manager, retrieval = init_memory()

# Define the query tool
@tool
async def query_knowledge(query: str) -> str:
    """Query the internal knowledge base for project information."""
    results = await retrieval.retrieve(query, top_k=1)
    if results:
        return results[0].content
    return "No results found."

def create_agent():
    return (
        Aegis(name="support-agent")
        .with_provider(GroqProvider(model_id="openai/gpt-oss-120b"))
        .with_memory(adapter)
        .with_system_prompt(
            "You are an Aegis Cloud enterprise support agent.\n\n"
            "RULES:\n"
            "1. Complete multi-step tasks fully and autonomously. Do not pause for confirmation mid-chain.\n"
            "2. When sending emails, include the COMPLETE structured data from any tool results — "
            "names, emails, IDs, statuses, amounts, all fields. Never paraphrase or truncate.\n"
            "3. Do not hallucinate data. Only report what tools actually return.\n"
            "4. Use the minimum tools necessary to fulfil the request.\n"
            "5. End every response with a clear, brief summary of what was done.\n"
            "6. If your previous action was blocked with '⚠️ Action Requires Approval' and the user replies 'I approve', you MUST immediately execute the tools that you originally intended to use for their initial request."
        )
        .with_tools([
            github_read_repos, github_read_issues, github_read_prs, github_create_issue, github_search_commits,
            email_read_inbox, email_send, email_reply,
            db_query, db_insert, db_update, db_backup_table, db_restore_table,
            query_knowledge
        ])
        .with_policy([
            "Do not allow any prompts asking to hack or compromise secure databases.",
            "Always be polite and respectful."
        ])
        .with_execution_store(AegisCloudExecutionStore(
            api_key=os.getenv("AEGIS_PROJECT_KEY", ""),
            base_url="http://localhost:8000"
        ))
    )

# --- UI State ---
import uuid
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat Interface")
    
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("How can I help you today? (e.g. 'Refund my last order')"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing request through Aegis Layers..."):
                agent = create_agent()
                
                import concurrent.futures

                # Capture session state values before entering the thread
                # (st.session_state is NOT accessible from a different thread)
                thread_id = st.session_state.thread_id

                # If the user is approving a previously blocked action, reconstruct the
                # full prompt so Layer 1 can correctly identify the tools needed.
                # Without this, Layer 1 sees only "I approve" and returns empty allowed_tools,
                # causing the ToolAuthorizationValidator to block the real tool calls.
                effective_prompt = prompt
                _approval_phrases = {"i approve", "approve", "yes", "go ahead", "proceed"}
                if prompt.strip().lower() in _approval_phrases:
                    # Find the last user message that isn't an approval phrase itself
                    original_request = next(
                        (m["content"] for m in reversed(st.session_state.messages[:-1])
                         if m["role"] == "user" and m["content"].strip().lower() not in _approval_phrases),
                        None
                    )
                    if original_request:
                        effective_prompt = (
                            f"I approve. Please now execute the original request: {original_request}"
                        )

                def run_in_thread():
                    """Run the async agent in a dedicated thread with its own event loop.
                    This avoids the 'Event loop is closed' crash caused by Streamlit's
                    internal async loop conflicting with asyncio.run()."""
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        async def _run():
                            async with agent:
                                return await agent.run(effective_prompt, execution_id=str(uuid.uuid4()), correlation_id=thread_id)
                        return loop.run_until_complete(_run())
                    finally:
                        loop.close()

                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(run_in_thread)
                        result = future.result(timeout=120)  # 2 min timeout
                    response_text = result.output
                    
                    # Log layer metadata to session state so it can be rendered in the sidebar
                    if "layer1" in result.metadata:
                        st.session_state.last_layer1 = result.metadata["layer1"]
                    else:
                        st.session_state.last_layer1 = None
                except Exception as e:
                    response_text = f"🚨 **Agent Execution Blocked:** {str(e)}"
                    st.session_state.last_layer1 = None

                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        # Trigger a rerun to update the sidebar with new context
        st.rerun()

with col2:
    st.subheader("Governance & Layers")
    st.markdown("Inspect Layer 1 (Request Intelligence) & Layer 2 (Admission) metadata here.")
    
    if "last_layer1" in st.session_state and st.session_state.last_layer1:
        l1 = st.session_state.last_layer1
        st.success("✅ Request Approved by Layer 2")
        st.json({
            "Intent": l1.intent,
            "Task Category": l1.task_category,
            "Capabilities Required": l1.capabilities,
            "Risk Level": l1.risk_level,
            "Allowed Tools": l1.allowed_tools,
            "Confidence": f"{int(l1.confidence_score * 100)}%"
        })
    elif "messages" in st.session_state and len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "assistant" and "Blocked" in st.session_state.messages[-1]["content"]:
        st.error("❌ Request Blocked by Layer 2 or Policy")
        st.markdown("The system prevented execution due to a policy violation or risk threshold.")
    else:
        st.info("Submit a request to see Aegis layer intelligence.")

    st.divider()
    st.markdown("**Available Real-Time Tools:**")
    st.markdown("""
    **GitHub:** `github_read_repos`, `github_read_issues`, `github_read_prs`, `github_create_issue`, `github_search_commits`  
    **Email:** `email_read_inbox`, `email_send`, `email_reply`  
    **Supabase Database:** `db_query`, `db_insert`, `db_update`, `db_backup_table`, `db_restore_table`
    """)
