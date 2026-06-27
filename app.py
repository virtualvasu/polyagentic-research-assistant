# app.py

import streamlit as st
import os
from dotenv import load_dotenv
from graph import app
import time

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    layout="wide"
)

# --- Brutalist CSS Injection ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Space+Mono:ital,wght@0,400;0,700;1,400;1,700&display=swap');

/* Brutalist Theme Colors & Variables */
:root {
    --bg-color: #d6d6d6;
    --text-color: #111111;
    --accent-color: #ff3c00; /* Harsh orange-red */
    --border-color: #111111;
    --border-width: 4px;
    --shadow-offset: 6px;
}

/* Global Font and Color Override */
html, body, p, span, div, label, li, [class*="css"], [class*="st-"] {
    font-family: 'Space Mono', monospace !important;
    color: var(--text-color) !important;
}

/* App Background */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg-color);
    background-image: radial-gradient(#111111 1px, transparent 1px);
    background-size: 20px 20px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #e8e8e8 !important;
    border-right: var(--border-width) solid var(--border-color);
}
[data-testid="stSidebar"]::before {
    content: 'SYSTEM.CONFIG';
    font-family: 'Anton', sans-serif;
    font-size: 3rem;
    color: var(--border-color);
    opacity: 0.1;
    position: absolute;
    top: 10px;
    left: 10px;
    pointer-events: none;
}

/* Typography for Headers */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Anton', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-color);
}

h1 {
    font-size: 4.5rem !important;
    color: var(--accent-color);
    text-shadow: 5px 5px 0px var(--border-color);
    margin-bottom: 0.5rem !important;
    line-height: 1.1 !important;
}

h2 {
    font-size: 2.5rem !important;
    background-color: var(--border-color);
    color: #ffffff;
    display: inline-block;
    padding: 0 10px;
    box-shadow: 4px 4px 0px var(--accent-color);
}

/* Dividers */
hr {
    border-top: var(--border-width) solid var(--border-color) !important;
    margin: 2rem 0 !important;
}

/* Buttons */
.stButton > button {
    background-color: var(--accent-color) !important;
    color: #ffffff !important;
    border: var(--border-width) solid var(--border-color) !important;
    border-radius: 0 !important;
    font-family: 'Anton', sans-serif !important;
    font-size: 1.5rem !important;
    padding: 0.5rem 1rem !important;
    text-transform: uppercase;
    box-shadow: var(--shadow-offset) var(--shadow-offset) 0px var(--border-color) !important;
    transition: all 0.1s ease-in-out;
}
.stButton > button:hover {
    background-color: #000000 !important;
    color: var(--accent-color) !important;
    box-shadow: 2px 2px 0px var(--border-color) !important;
    transform: translate(4px, 4px);
}
.stButton > button:active {
    box-shadow: 0px 0px 0px var(--border-color) !important;
    transform: translate(6px, 6px);
}

/* Inputs & Selectboxes */
.stTextInput > div > div > input, .stSelectbox > div > div > div {
    background-color: #ffffff !important;
    border: var(--border-width) solid var(--border-color) !important;
    border-radius: 0 !important;
    color: var(--text-color) !important;
    box-shadow: var(--shadow-offset) var(--shadow-offset) 0px var(--border-color) !important;
    font-size: 1.2rem !important;
}
.stTextInput > div > div > input:focus, .stSelectbox > div > div > div:focus {
    box-shadow: inset 4px 4px 0px var(--accent-color) !important;
    outline: none !important;
}

/* Containers / Metrics / Expanders */
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
    font-family: 'Anton', sans-serif !important;
}
div[data-testid="metric-container"] {
    background-color: #ffffff;
    border: var(--border-width) solid var(--border-color);
    box-shadow: 4px 4px 0px var(--border-color);
    padding: 1rem;
}
.stExpander {
    border: var(--border-width) solid var(--border-color) !important;
    border-radius: 0 !important;
    background-color: #ffffff !important;
    box-shadow: 4px 4px 0px var(--border-color);
    margin-bottom: 1rem;
}

/* Progress Bar */
.stProgress > div > div > div > div {
    background-color: var(--accent-color) !important;
}
.stProgress > div > div {
    background-color: #ffffff !important;
    border: 2px solid var(--border-color) !important;
    border-radius: 0 !important;
}

/* Toast/Alert Boxes */
div[data-testid="stAlert"] {
    border: var(--border-width) solid var(--border-color) !important;
    border-radius: 0 !important;
    box-shadow: 4px 4px 0px var(--border-color) !important;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# --- Check for API Keys ---
def check_api_keys(provider):
    """Check if required API keys are present based on provider."""
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        st.error("API keys not found! Please set TAVILY_API_KEY in your .env file.")
        return False
        
    if provider == "groq":
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            st.error("API keys not found! Please set GROQ_API_KEY in your .env file.")
            return False
    
    st.success("API keys loaded successfully.")
    return True

# --- Header ---
st.title("Multi-Agent Research Assistant")
st.markdown("""
Welcome to your intelligent research assistant! 
Enter a research topic, and a team of AI agents will collaborate to produce a comprehensive report.

**Agent Team:**
- **Supervisor**: Manages the workflow and coordinates tasks
- **Researcher**: Gathers information using web search
- **Writer**: Creates and revises the research report
- **Critiquer**: Reviews drafts and provides feedback
""")

st.divider()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Configuration")
    max_iterations = st.slider(
        "Max Workflow Iterations",
        min_value=5,
        max_value=25,
        value=15,
        help="Maximum number of agent interactions"
    )
    
    st.divider()
    st.header("LLM Configuration")
    
    llm_provider = st.selectbox(
        "LLM Provider",
        options=["Groq", "Ollama"],
        index=0,
        help="Choose the LLM backend to run the agents"
    )
    
    if llm_provider == "Groq":
        llm_model = st.selectbox(
            "Model Name",
            options=[
                "llama-3.3-70b-versatile",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ],
            index=0,
            help="Select the Groq model to use"
        )
        ollama_url = ""
    else:
        ollama_models = os.environ.get("OLLAMA_MODELS", "llama3.1:latest,llama3.1:8b,qwen2.5:7b").split(",")
        llm_model = st.selectbox(
            "Model Name",
            options=[m.strip() for m in ollama_models if m.strip()],
            index=0,
            help="Select your local Ollama model"
        )
        
        default_ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_url = st.text_input(
            "Ollama Host URL",
            value=default_ollama_url,
            help="URL to your local Ollama instance"
        )
    
    st.divider()
    st.subheader("How it works")
    st.markdown("""
    1. **Supervisor** analyzes the task
    2. **Researcher** gathers information
    3. **Writer** creates a draft
    4. **Critiquer** reviews quality
    5. Loop continues until approved
    """)

# --- Check API Keys ---
if not check_api_keys(llm_provider.lower()):
    st.stop()

# --- Main Application ---
import uuid


if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "run_status" not in st.session_state:
    st.session_state.run_status = "idle"
if "all_states" not in st.session_state:
    st.session_state.all_states = []
if "final_state" not in st.session_state:
    st.session_state.final_state = None
if "step_count" not in st.session_state:
    st.session_state.step_count = 0

st.header("Start Your Research")

# User input
topic = st.text_input(
    "Enter your research topic:",
    placeholder="e.g., Impact of quantum computing on cybersecurity",
    key="topic_input"
)

if st.button("Start / Restart Research", type="primary"):
    if not topic:
        st.error("Please enter a research topic.")
    else:
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.run_status = "running"
        st.session_state.all_states = []
        st.session_state.final_state = None
        st.session_state.step_count = 0
        st.rerun()

config = {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": max_iterations}

def process_stream(stream_obj):
    progress_bar = st.progress(0)
    progress_container = st.container()
    
    with progress_container:
        st.subheader("Agent Activity Log")
        
        for step in stream_obj:
            st.session_state.step_count += 1
            progress_bar.progress(min(st.session_state.step_count / max_iterations, 1.0))
            
            node_name = list(step.keys())[0]
            node_output = step[node_name]
            
            st.session_state.all_states.append((node_name, node_output))
            st.session_state.final_state = node_output
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### Agent: `{node_name.upper()}`")
                with col2:
                    st.caption(f"Step {st.session_state.step_count}")
                
                if node_name == "supervisor":
                    st.markdown(f"**Decision:** {node_output.get('next_step', 'N/A')}")
                    st.markdown(f"**Task:** {node_output.get('current_sub_task', 'N/A')}")
                elif node_name == "researcher":
                    findings = node_output.get('research_findings', [])
                    if findings:
                        st.success("Research completed")
                        latest = findings[-1]
                        with st.expander(f"Show Full Research (Step {st.session_state.step_count})"):
                            st.markdown(latest)
                elif node_name == "writer":
                    draft = node_output.get('draft', '')
                    st.success(f"Draft {node_output.get('revision_number', 0)} generated ({len(draft)} chars)")
                    with st.expander(f"Show Full Draft (Step {st.session_state.step_count})"):
                        st.markdown(draft)
                elif node_name == "critiquer":
                    critique = node_output.get('critique_notes', '')
                    if "APPROVED" in critique.upper():
                        st.success("Draft APPROVED!")
                    else:
                        st.warning("Revisions requested")
                    with st.expander(f"Show Full Critique (Step {st.session_state.step_count})"):
                        st.markdown(critique)
                elif node_name == "human_review":
                    st.info("Human review required.")
                
                st.divider()
            time.sleep(0.3)
            
    # After stream finishes, check if it's paused
    state = app.get_state(config)
    if state.next and "human_review" in state.next:
        st.session_state.run_status = "paused_at_review"
        st.rerun()
    elif not state.next:
        st.session_state.run_status = "completed"
        progress_bar.progress(1.0)
        st.rerun()

# --- Execution Flow ---

if st.session_state.run_status == "running":
    st.info("Agents are working...")
    
    # If starting fresh
    if st.session_state.step_count == 0:
        initial_state = {
            "main_task": topic,
            "research_findings": [],
            "draft": "",
            "critique_notes": "",
            "revision_number": 0,
            "next_step": "",
            "current_sub_task": "",
            "llm_provider": llm_provider.lower(),
            "llm_model": llm_model,
            "ollama_url": ollama_url,
            "hitl_approved": False,
            "hitl_edited_findings": ""
        }
        stream_obj = app.stream(initial_state, config=config)
    else:
        # Resuming from a state
        stream_obj = app.stream(None, config=config)
        
    try:
        process_stream(stream_obj)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.session_state.run_status = "error"

elif st.session_state.run_status == "paused_at_review":
    st.warning("⏸️ Workflow Paused: Research Review Gate")
    st.markdown("Please review the findings before the Writer drafts the report.")
    
    # Get current state
    current_state = app.get_state(config).values
    findings = current_state.get("research_findings", [])
    latest_findings = findings[-1] if findings else "No findings available."
    
    edited_text = st.text_area("Research Findings (Edit if necessary):", value=latest_findings, height=300)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Proceed to Writer", type="primary", use_container_width=True):
            app.update_state(config, {"hitl_edited_findings": edited_text, "hitl_approved": True, "next_step": "supervisor"}, as_node="human_review")
            st.session_state.run_status = "running"
            st.rerun()
            
    with col2:
        new_query = st.text_input("New query for Re-search:")
        if st.button("Re-search", use_container_width=True):
            if new_query:
                app.update_state(config, {"current_sub_task": new_query, "next_step": "researcher"}, as_node="human_review")
                st.session_state.run_status = "running"
                st.rerun()
            else:
                st.error("Please enter a query to re-search.")

elif st.session_state.run_status == "completed":
    st.success("Research Complete!")
    
    st.divider()
    
    final_state = app.get_state(config).values
    final_draft = final_state.get("draft", "")
                    
    if final_draft and len(final_draft.strip()) > 50:
        st.header("Final Research Report")
        
        with st.container():
            st.markdown(final_draft)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Report Statistics")
            st.metric("Revisions", final_state.get("revision_number", 0) if isinstance(final_state, dict) else 0)
            st.metric("Word Count", len(final_draft.split()))
            
        with col2:
            st.subheader("Research Findings")
            if isinstance(final_state, dict) and final_state.get("research_findings"):
                with st.expander("View all research data"):
                    for idx, finding in enumerate(final_state.get("research_findings", []), 1):
                        st.markdown(f"**Finding {idx}:**")
                        st.write(finding)
                        
        st.download_button(
            label="Download Report",
            data=final_draft,
            file_name=f"research_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.error("No report was generated. Please try again.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Powered by LangChain, LangGraph, Groq & Tavily</p>
</div>
""", unsafe_allow_html=True)