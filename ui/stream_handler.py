import streamlit as st
import time

# ── Agent metadata — zero emojis, numbered typographic labels ────────────────
AGENTS = [
    {"key": "supervisor",   "num": "01", "abbr": "SV", "label": "Supervisor"},
    {"key": "researcher",   "num": "02", "abbr": "RS", "label": "Researcher"},
    {"key": "human_review", "num": "03", "abbr": "HU", "label": "Review"},
    {"key": "writer",       "num": "04", "abbr": "WR", "label": "Writer"},
    {"key": "critiquer",    "num": "05", "abbr": "CR", "label": "Critiquer"},
]

PIPELINE_ORDER = [a["key"] for a in AGENTS]


def _pipeline_html(active_agent: str | None = None) -> str:
    """Generates the pipeline bar HTML (used for live placeholder updates)."""
    completed = st.session_state.get("completed_agents", [])
    html = '<div class="pipeline-bar">'
    for agent in AGENTS:
        key       = agent["key"]
        is_active = key == active_agent
        is_done   = key in completed and not is_active

        if is_active:
            css   = "pipeline-step active"
            badge = "RUNNING"
        elif is_done:
            css   = "pipeline-step done"
            badge = "DONE"
        else:
            css   = "pipeline-step"
            badge = "QUEUED"

        html += f"""<div class="{css}">
            <span class="step-num">{agent["num"]}</span>
            <span class="step-label">{agent["label"].upper()}</span>
            <span class="step-status">{badge}</span>
        </div>"""
    html += "</div>"
    return html


def render_pipeline_header(active_agent: str | None = None):
    """Renders the always-visible horizontal pipeline status bar."""
    st.markdown(_pipeline_html(active_agent), unsafe_allow_html=True)


def _downgrade_headers(text: str) -> str:
    """
    Downgrade markdown heading levels so findings don't render
    as giant h1/h2 styled by the global brutalist CSS.
    # Title   -> #### Title  (h4)
    ## Title  -> ##### Title (h5)
    ### Title -> ###### Title (h6)
    """
    lines = []
    for line in text.split("\n"):
        if line.startswith("### "):
            lines.append("###### " + line[4:])
        elif line.startswith("## "):
            lines.append("##### " + line[3:])
        elif line.startswith("# "):
            lines.append("#### " + line[2:])
        else:
            lines.append(line)
    return "\n".join(lines)


def _render_research_brief(findings_text: str, step: int, elapsed: float):
    """Renders a compact header strip + plain markdown for research findings."""
    word_count = len(findings_text.split())
    safe_text  = _downgrade_headers(findings_text)

    # Compact header strip
    st.markdown(f"""
    <div class="research-brief-header">
        <span>RESEARCH BRIEF</span>
        <span class="research-brief-meta">STEP {step:02d} &nbsp;&mdash;&nbsp; {word_count} WORDS &nbsp;&mdash;&nbsp; {elapsed:.0f}s</span>
    </div>
    """, unsafe_allow_html=True)

    # Render findings with downgraded headers — no giant h1/h2
    st.markdown(safe_text)


def _render_agent_card_header(node_name: str, step: int, elapsed: float):
    """Renders the dark colored header bar for an agent step card."""
    meta  = next((a for a in AGENTS if a["key"] == node_name), {"num": "--", "abbr": "??", "label": node_name})
    label = meta["label"].upper()
    abbr  = meta["abbr"]

    st.markdown(f"""
    <div class="agent-card-header {node_name}">
        <span class="agent-name"><span class="agent-abbr">[{abbr}]</span> &nbsp; {label}</span>
        <span class="agent-meta">STEP {step:02d} &nbsp;&mdash;&nbsp; {elapsed:.0f}s</span>
    </div>
    """, unsafe_allow_html=True)


def process_stream(stream_obj, app, config, max_iterations):
    """Processes the LangGraph execution stream and renders styled UI for each step."""

    if "completed_agents" not in st.session_state:
        st.session_state.completed_agents = []

    progress_bar         = st.progress(0)
    pipeline_placeholder = st.empty()

    st.markdown("---")
    st.markdown(
        '<p style="font-family: Anton, sans-serif; font-size:1rem; letter-spacing:4px; '
        'text-transform:uppercase; color:#888; margin:0 0 1rem 0;">// AGENT ACTIVITY LOG</p>',
        unsafe_allow_html=True
    )

    step_start = time.time()

    for step in stream_obj:
        st.session_state.step_count += 1
        progress_bar.progress(min(st.session_state.step_count / max_iterations, 1.0))

        node_name   = list(step.keys())[0]
        node_output = step[node_name]
        elapsed     = time.time() - step_start
        step_start  = time.time()

        st.session_state.all_states.append((node_name, node_output))
        st.session_state.final_state = node_output

        # Live-update the pipeline header
        pipeline_placeholder.markdown(_pipeline_html(node_name), unsafe_allow_html=True)

        # Track completed agents
        if node_name not in st.session_state.completed_agents:
            st.session_state.completed_agents.append(node_name)

        # ── Render agent card ─────────────────────────────────────────────
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        _render_agent_card_header(node_name, st.session_state.step_count, elapsed)
        st.markdown('<div class="agent-card-body">', unsafe_allow_html=True)

        if node_name == "supervisor":
            decision = node_output.get("next_step", "N/A")
            task     = node_output.get("current_sub_task", "N/A")
            st.markdown(f"**ROUTE &rarr;** `{decision.upper()}`")
            st.markdown(f"**TASK:** {task}")

        elif node_name == "researcher":
            findings = node_output.get("research_findings", [])
            if findings:
                _render_research_brief(findings[-1], st.session_state.step_count, elapsed)
            else:
                st.warning("No findings returned.")

        elif node_name == "writer":
            draft   = node_output.get("draft", "")
            rev_num = node_output.get("revision_number", 0)
            st.success(f"Draft v{rev_num} generated — {len(draft.split())} words")
            with st.expander("PREVIEW DRAFT"):
                st.markdown(draft)

        elif node_name == "critiquer":
            critique = node_output.get("critique_notes", "")
            if "APPROVED" in critique.upper():
                st.success("APPROVED — proceeding to final report.")
            else:
                st.warning("REVISIONS REQUESTED.")
                with st.expander("VIEW CRITIQUE NOTES"):
                    st.markdown(critique)

        elif node_name == "human_review":
            st.info("Workflow paused — awaiting your review.")

        st.markdown("</div></div>", unsafe_allow_html=True)
        st.toast(f"{node_name.replace('_', ' ').title()} finished processing.")
        time.sleep(0.2)

    # ── After stream ends ─────────────────────────────────────────────────
    state = app.get_state(config)
    if state.next and "human_review" in state.next:
        st.session_state.run_status = "paused_at_review"
        st.rerun()
    elif not state.next:
        st.session_state.run_status = "completed"
        progress_bar.progress(1.0)
        st.rerun()
