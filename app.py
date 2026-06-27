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
        llm_model = st.text_input(
            "Model Name",
            value="llama3.3",
            help="Enter the model name pulled in Ollama (e.g., llama3.3, mistral, llama3, phi3)"
        )
        ollama_url = st.text_input(
            "Ollama Host URL",
            value="http://localhost:11434",
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
st.header("Start Your Research")

# User input
topic = st.text_input(
    "Enter your research topic:",
    placeholder="e.g., Impact of quantum computing on cybersecurity",
    key="topic_input"
)

# Start button
if st.button("Start Research", type="primary", use_container_width=True):
    if not topic:
        st.error("Please enter a research topic.")
    else:
        # Define the initial state
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
            "ollama_url": ollama_url
        }
        
        # Configuration
        config = {"recursion_limit": max_iterations}
        
        st.info("Agents are starting their work...")
        
        # Create containers for live updates
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        # Container for step-by-step progress
        progress_container = st.container()
        
        final_state = None
        step_count = 0
        all_states = []  # Keep track of all states
        
        try:
            # Stream the graph execution
            with progress_container:
                st.subheader("Agent Activity Log")
                
                for step in app.stream(initial_state, config=config):
                    step_count += 1
                    progress_bar.progress(min(step_count / max_iterations, 1.0))
                    
                    # Get node name and output
                    node_name = list(step.keys())[0]
                    node_output = step[node_name]
                    
                    # Store the complete state
                    all_states.append((node_name, node_output))
                    final_state = node_output  # Keep updating final state
                    
                    # Display node output with expandable previews
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"### Agent: `{node_name.upper()}`")
                        
                        with col2:
                            st.caption(f"Step {step_count}")
                        
                        if node_name == "supervisor":
                            next_step = node_output.get('next_step', 'N/A')
                            task = node_output.get('current_sub_task', 'N/A')
                            st.markdown(f"**Decision:** {next_step}")
                            st.markdown(f"**Task:** {task}")
                        
                        elif node_name == "researcher":
                            findings = node_output.get('research_findings', [])
                            if findings:
                                latest = findings[-1]
                                st.success("Research completed")
                                
                                # Preview with "Show More" button
                                preview_length = 300
                                if len(latest) > preview_length:
                                    st.markdown("**Research Preview:**")
                                    st.info(latest[:preview_length] + "...")
                                    
                                    # Unique key for each expander
                                    with st.expander(f"Show Full Research (Step {step_count})"):
                                        st.markdown(latest)
                                else:
                                    st.markdown("**Research:**")
                                    st.info(latest)
                        
                        elif node_name == "writer":
                            draft = node_output.get('draft', '')
                            revision = node_output.get('revision_number', 0)
                            st.success(f"Draft {revision} generated ({len(draft)} chars)")
                            
                            # Preview with "Show More" button
                            preview_length = 400
                            if len(draft) > preview_length:
                                st.markdown("**Draft Preview:**")
                                st.info(draft[:preview_length] + "...")
                                
                                # Unique key for each expander
                                with st.expander(f"Show Full Draft (Step {step_count})"):
                                    st.markdown(draft)
                            else:
                                st.markdown("**Draft:**")
                                st.info(draft)
                        
                        elif node_name == "critiquer":
                            critique = node_output.get('critique_notes', '')
                            if "APPROVED" in critique.upper():
                                st.success("Draft APPROVED!")
                            else:
                                st.warning("Revisions requested")
                            
                            # Preview with "Show More" button
                            preview_length = 300
                            if len(critique) > preview_length:
                                st.markdown("**Critique Preview:**")
                                st.info(critique[:preview_length] + "...")
                                
                                # Unique key for each expander
                                with st.expander(f"Show Full Critique (Step {step_count})"):
                                    st.markdown(critique)
                            else:
                                st.markdown("**Critique:**")
                                st.info(critique)
                        
                        st.divider()
                    
                    time.sleep(0.3)
            
            # Update status when done
            status_placeholder.success("Research Complete!")
            progress_bar.progress(1.0)
            
            # Debug: Print final state info
            print(f"Final state type: {type(final_state)}")
            print(f"Final state keys: {final_state.keys() if isinstance(final_state, dict) else 'Not a dict'}")
            print(f"Draft exists: {bool(final_state.get('draft') if isinstance(final_state, dict) else False)}")
            print(f"Draft length: {len(final_state.get('draft', '')) if isinstance(final_state, dict) else 0}")
            
        except Exception as e:
            status_placeholder.error("Error occurred")
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)
            final_state = None
        
        # Display final report - IMPROVED LOGIC
        st.divider()
        
        # Try to get the draft from final_state
        final_draft = None
        if final_state and isinstance(final_state, dict):
            final_draft = final_state.get("draft", "")
        
        # If no draft in final_state, search through all states
        if not final_draft or len(final_draft.strip()) < 50:
            print("Searching for draft in all states...")
            for node_name, state in reversed(all_states):
                if isinstance(state, dict) and state.get("draft"):
                    draft_candidate = state.get("draft", "")
                    if len(draft_candidate.strip()) > 50:
                        final_draft = draft_candidate
                        final_state = state
                        print(f"Found draft in {node_name} state")
                        break
        
        if final_draft and len(final_draft.strip()) > 50:
            st.header("Final Research Report")
            
            # Display report in a nice container
            with st.container():
                st.markdown(final_draft)
            
            st.divider()
            
            # Display metadata
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Report Statistics")
                revision_count = final_state.get("revision_number", 0) if isinstance(final_state, dict) else 0
                research_count = len(final_state.get("research_findings", [])) if isinstance(final_state, dict) else 0
                word_count = len(final_draft.split())
                
                st.metric("Revisions", revision_count)
                st.metric("Research Sources", research_count)
                st.metric("Word Count", word_count)
                st.metric("Character Count", len(final_draft))
            
            with col2:
                st.subheader("Research Findings")
                if isinstance(final_state, dict) and final_state.get("research_findings"):
                    # Use expander here (safe, outside of workflow)
                    with st.expander("View all research data", expanded=False):
                        for idx, finding in enumerate(final_state.get("research_findings", []), 1):
                            st.markdown(f"**Finding {idx}:**")
                            st.write(finding)
                            if idx < len(final_state.get("research_findings", [])):
                                st.divider()
                else:
                    st.info("No research findings available")
            
            # Download button
            st.download_button(
                label="Download Report",
                data=final_draft,
                file_name=f"research_report_{topic.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.error("No report was generated. Please try again.")
            if final_state:
                with st.expander("Debug: View Final State"):
                    st.json(final_state if isinstance(final_state, dict) else {"error": "State is not a dictionary"})

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Powered by LangChain, LangGraph, Groq & Tavily</p>
</div>
""", unsafe_allow_html=True)