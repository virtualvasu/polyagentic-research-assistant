import os
import streamlit as st
import uuid

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

def init_session_state():
    """Initializes all necessary session state variables."""
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
