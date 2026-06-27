# app.py

import streamlit as st
import os
import uuid
from dotenv import load_dotenv
from graph import app

from ui.style import apply_brutalist_theme
from ui.sidebar import render_sidebar
from ui.state import check_api_keys, init_session_state
from ui.stream_handler import process_stream, render_pipeline_header, _pipeline_html, _downgrade_headers

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    layout="wide"
)

# --- Brutalist CSS Injection ---
apply_brutalist_theme()

# --- Header ---
st.title("Multi-Agent Research Assistant")
st.markdown("""
A team of AI agents will collaborate to research your topic and produce a polished report.
Configure the workflow in the sidebar, enter your topic, and hit **Start**.
""")

st.divider()

# --- Sidebar Configuration ---
max_iterations, llm_provider, llm_model, ollama_url = render_sidebar()

# --- Check API Keys ---
if not check_api_keys(llm_provider.lower()):
    st.stop()

# --- State Initialization ---
init_session_state()

# ── Helper: render the structured final report ────────────────────────────────
def render_structured_report(report_text: str):
    """
    Parses the markdown report (with ## headers) and renders each section
    as a distinct styled block rather than a raw markdown dump.
    """
    # Split on level-2 headers
    import re
    # Split keeping the section title
    parts = re.split(r"(?m)^##\s+", report_text)

    sections = []
    # First part before any ## is preamble (usually empty)
    for part in parts[1:]:
        lines     = part.strip().split("\n", 1)
        title     = lines[0].strip()
        body      = lines[1].strip() if len(lines) > 1 else ""
        sections.append((title, body))

    if not sections:
        # Fallback: just render raw markdown
        st.markdown(report_text)
        return

    # Build the wrapper
    st.markdown('<div class="report-wrapper">', unsafe_allow_html=True)

    # Title bar
    word_count = len(report_text.split())
    st.markdown(f'<div class="report-title-bar"><span>FINAL RESEARCH REPORT</span><span style="font-family: Space Mono; font-size:0.7rem; color: rgba(255,255,255,0.6);">{word_count} WORDS</span></div>', unsafe_allow_html=True)

    for title, body in sections:
        title_upper = title.upper()

        if "KEY TAKEAWAY" in title_upper or "TAKEAWAY" in title_upper:
            st.markdown(f'<div class="report-key-takeaway"><span class="report-section-label">-- KEY TAKEAWAY</span>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:#ffffff; font-size:1.05rem;">{body}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif "BOTTOM LINE" in title_upper or "CONCLUSION" in title_upper:
            st.markdown(f'<div class="report-bottom-line"><span class="report-section-label">-- BOTTOM LINE</span>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:#ffffff;">{body}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif "ANALYSIS" in title_upper:
            st.markdown(f'<div class="report-section report-analysis"><span class="report-section-label">// {title.upper()}</span>', unsafe_allow_html=True)
            st.markdown(body)
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.markdown(f'<div class="report-section"><span class="report-section-label">// {title.upper()}</span>', unsafe_allow_html=True)
            st.markdown(body)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# IDLE / INPUT STATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.run_status == "idle":
    render_pipeline_header(active_agent=None)

    st.markdown("### Start Your Research")
    topic = st.text_input(
        "Enter your research topic:",
        placeholder="e.g., Impact of quantum computing on cybersecurity",
        key="topic_input"
    )

    if st.button("START RESEARCH", type="primary"):
        if not topic:
            st.error("Please enter a research topic.")
        else:
            st.session_state.thread_id  = str(uuid.uuid4())
            st.session_state.run_status = "running"
            st.session_state.all_states = []
            st.session_state.final_state = None
            st.session_state.step_count  = 0
            st.session_state.completed_agents = []
            st.session_state.topic = topic
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# RUNNING STATE
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.run_status == "running":

    config = {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": max_iterations}
    topic  = st.session_state.get("topic", "")

    st.info("Agents are working — this may take a minute...")

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
        stream_obj = app.stream(None, config=config)

    try:
        process_stream(stream_obj, app, config, max_iterations)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.session_state.run_status = "error"

    # Always show a restart button
    if st.button("START OVER"):
        st.session_state.run_status      = "idle"
        st.session_state.completed_agents = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# HUMAN REVIEW (HITL) GATE
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.run_status == "paused_at_review":

    config = {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": max_iterations}

    # Show pipeline with human_review as active
    st.markdown(_pipeline_html("human_review"), unsafe_allow_html=True)

    # Big orange banner
    st.markdown("""
    <div class="hitl-banner">
        <div class="hitl-banner-icon">[ PAUSE ]</div>
        <div class="hitl-banner-text">
            <h3>Awaiting Your Review</h3>
            <p>The Researcher has finished. Review and optionally edit the findings before the Writer begins drafting the report.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Get state
    current_state   = app.get_state(config).values
    findings        = current_state.get("research_findings", [])
    latest_findings = findings[-1] if findings else "No findings available."

    col_read, col_edit = st.columns(2)

    with col_read:
        st.markdown('<span class="hitl-panel-label">RESEARCH FINDINGS &mdash; READ ONLY</span>', unsafe_allow_html=True)
        st.markdown('<div class="hitl-panel">', unsafe_allow_html=True)
        st.markdown(_downgrade_headers(latest_findings))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Word count signal
        wc = len(latest_findings.split())
        st.caption(f"{wc} words in findings")

    with col_edit:
        st.markdown('<span class="hitl-panel-label">EDIT BEFORE SENDING TO WRITER</span>', unsafe_allow_html=True)
        edited_text = st.text_area(
            label="",
            value=latest_findings,
            height=340,
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("APPROVE + WRITE", type="primary", use_container_width=True):
                app.update_state(
                    config,
                    {"hitl_edited_findings": edited_text, "hitl_approved": True, "next_step": "supervisor"},
                    as_node="human_review"
                )
                st.session_state.run_status = "running"
                st.rerun()

        with btn_col2:
            new_query = st.text_input("Re-search query:", placeholder="Enter a new query…")
            if st.button("RE-SEARCH", use_container_width=True):
                if new_query:
                    app.update_state(
                        config,
                        {"current_sub_task": new_query, "next_step": "researcher"},
                        as_node="human_review"
                    )
                    st.session_state.run_status = "running"
                    st.rerun()
                else:
                    st.error("Please enter a query.")

# ─────────────────────────────────────────────────────────────────────────────
# COMPLETED STATE
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.run_status == "completed":

    config      = {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": max_iterations}
    final_state = app.get_state(config).values
    final_draft = final_state.get("draft", "")

    # Show full pipeline as done
    all_done_html = _pipeline_html(active_agent=None)
    st.markdown(all_done_html, unsafe_allow_html=True)
    st.success("Research Complete.")
    st.divider()

    if final_draft and len(final_draft.strip()) > 50:
        render_structured_report(final_draft)

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Report Statistics")
            rev_num = final_state.get("revision_number", 0) if isinstance(final_state, dict) else 0
            st.metric("Revisions", rev_num)
            st.metric("Word Count", len(final_draft.split()))

        with col2:
            st.subheader("Source Findings")
            if isinstance(final_state, dict) and final_state.get("research_findings"):
                with st.expander("View All Research Data"):
                    for idx, finding in enumerate(final_state.get("research_findings", []), 1):
                        st.markdown(f"**Finding {idx}:**")
                        st.write(finding)

        st.download_button(
            label="DOWNLOAD REPORT (.txt)",
            data=final_draft,
            file_name="research_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.error("No report was generated. Please try again.")

    if st.button("START NEW RESEARCH"):
        st.session_state.run_status       = "idle"
        st.session_state.completed_agents = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ERROR STATE
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.run_status == "error":
    st.error("Something went wrong. Check logs or try again.")
    if st.button("START OVER"):
        st.session_state.run_status       = "idle"
        st.session_state.completed_agents = []
        st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p style="color:#888 !important;">Powered by LangChain · LangGraph · Groq · Tavily</p>
</div>
""", unsafe_allow_html=True)