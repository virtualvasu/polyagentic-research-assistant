import os
import streamlit as st

def render_sidebar():
    """Renders the sidebar and returns configuration parameters."""
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
            index=1,
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

        return max_iterations, llm_provider, llm_model, ollama_url
