import streamlit as st

def apply_brutalist_theme():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Space+Mono:ital,wght@0,400;0,700;1,400;1,700&display=swap');

/* Brutalist Theme Colors & Variables */
:root {
    --bg-color: #d6d6d6;
    --text-color: #111111;
    --accent-color: #ff3c00;
    --border-color: #111111;
    --border-width: 4px;
    --shadow-offset: 6px;
    --agent-supervisor: #1a1a2e;
    --agent-researcher: #16213e;
    --agent-writer: #0f3460;
    --agent-critiquer: #533483;
    --agent-human: #ff3c00;
}

/* Global Font and Color Override */
html, body, p, span, div, label, li, [class*="css"], [class*="st-"] {
    font-family: 'Space Mono', monospace !important;
    color: var(--text-color) !important;
}

/* App Background */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg-color);
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

/* Typography for Headers & Code */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Anton', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-color);
}

pre, code {
    background-color: #111111 !important;
    color: #ffffff !important;
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
    background-color: var(--border-color) !important;
    color: #ffffff !important;
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

/* Inputs, Selectboxes, & Textareas */
.stTextInput > div > div > input, .stSelectbox > div > div > div, .stTextArea > div > div > textarea {
    background-color: #ffffff !important;
    border: var(--border-width) solid var(--border-color) !important;
    border-radius: 0 !important;
    color: var(--text-color) !important;
    box-shadow: var(--shadow-offset) var(--shadow-offset) 0px var(--border-color) !important;
    font-size: 1.2rem !important;
}
.stTextInput > div > div > input:focus, .stSelectbox > div > div > div:focus, .stTextArea > div > div > textarea:focus {
    box-shadow: inset 4px 4px 0px var(--accent-color) !important;
    outline: none !important;
}

/* Dropdown Menus */
div[data-baseweb="popover"] ul, ul[role="listbox"], li[role="option"] {
    background-color: #ffffff !important;
    color: var(--text-color) !important;
    font-family: 'Space Mono', monospace !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
    background-color: var(--accent-color) !important;
    color: #ffffff !important;
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
[data-testid="stExpander"] {
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
    background-color: #ffffff !important;
    color: var(--text-color) !important;
    border: var(--border-width) solid var(--border-color) !important;
    border-radius: 0 !important;
    box-shadow: 4px 4px 0px var(--border-color) !important;
    font-weight: bold;
}

/* ============================================
   PIPELINE HEADER
   ============================================ */
.pipeline-bar {
    display: flex;
    align-items: stretch;
    gap: 0;
    margin: 1.5rem 0 2rem 0;
    border: var(--border-width) solid var(--border-color);
    box-shadow: var(--shadow-offset) var(--shadow-offset) 0px var(--border-color);
    overflow: hidden;
}
.pipeline-step {
    flex: 1;
    padding: 0.75rem 0.5rem;
    text-align: center;
    border-right: 2px solid var(--border-color);
    background-color: #ffffff;
    position: relative;
    transition: all 0.2s ease;
}
.pipeline-step:last-child { border-right: none; }
.pipeline-step .step-num {
    font-family: 'Anton', sans-serif;
    font-size: 1.6rem;
    display: block;
    line-height: 1;
    letter-spacing: 0;
}
.pipeline-step .step-label {
    font-family: 'Anton', sans-serif !important;
    font-size: 0.65rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #666 !important;
    display: block;
    margin-top: 2px;
}
.pipeline-step .step-status {
    font-size: 0.6rem;
    font-family: 'Space Mono', monospace !important;
    color: #999 !important;
    display: block;
}
.pipeline-step.done {
    background-color: var(--border-color);
}
.pipeline-step.done .step-label,
.pipeline-step.done .step-status,
.pipeline-step.done .step-icon {
    color: #ffffff !important;
}
.pipeline-step.active {
    background-color: var(--accent-color);
    animation: pulse-bg 1.5s ease-in-out infinite;
}
.pipeline-step.active .step-label,
.pipeline-step.active .step-status,
.pipeline-step.active .step-icon {
    color: #ffffff !important;
}
@keyframes pulse-bg {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.82; }
}

/* ============================================
   AGENT ACTIVITY CARDS
   ============================================ */
.agent-card {
    background: #ffffff;
    border: var(--border-width) solid var(--border-color);
    box-shadow: 4px 4px 0px var(--border-color);
    margin-bottom: 1rem;
    overflow: hidden;
}
.agent-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 1rem;
    border-bottom: 2px solid var(--border-color);
}
.agent-card-header.supervisor { background-color: var(--agent-supervisor); }
.agent-card-header.researcher { background-color: var(--agent-researcher); }
.agent-card-header.writer     { background-color: var(--agent-writer); }
.agent-card-header.critiquer  { background-color: var(--agent-critiquer); }
.agent-card-header.human_review { background-color: var(--agent-human); }
.agent-name {
    font-family: 'Anton', sans-serif !important;
    font-size: 1.1rem;
    letter-spacing: 2px;
    color: #ffffff !important;
}
.agent-abbr {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.85rem;
    opacity: 0.65;
    color: #ffffff !important;
}
.agent-meta {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem;
    color: rgba(255,255,255,0.7) !important;
    text-align: right;
}
.agent-card-body {
    padding: 0.8rem 1rem;
    background: #ffffff;
}

/* ============================================
   RESEARCH BRIEF CARD
   ============================================ */
.research-brief {
    background: #ffffff;
    border: var(--border-width) solid var(--border-color);
    box-shadow: var(--shadow-offset) var(--shadow-offset) 0px var(--border-color);
    margin: 0.5rem 0;
    overflow: hidden;
}
.research-brief-header {
    background-color: var(--agent-researcher);
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.research-brief-header span {
    font-family: 'Anton', sans-serif !important;
    color: #ffffff !important;
    font-size: 1rem;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.research-brief-meta {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.6rem !important;
    color: rgba(255,255,255,0.6) !important;
}
.research-bullet-list {
    list-style: none;
    padding: 0.75rem 1rem;
    margin: 0;
    border-bottom: 2px solid var(--border-color);
}
.research-bullet-list li {
    padding: 0.3rem 0;
    font-size: 0.85rem;
    border-bottom: 1px dashed #ccc;
    color: var(--text-color) !important;
}
.research-bullet-list li:last-child { border-bottom: none; }
.research-bullet-list li::before {
    content: "▸ ";
    color: var(--accent-color) !important;
    font-weight: bold;
}

/* ============================================
   FINDINGS TEXT — plain, compact, no brutalist chrome
   ============================================ */
.findings-text {
    padding: 0.75rem 1rem;
    background: #fafafa;
    border-left: 3px solid #cccccc;
    margin-top: 0;
}
.findings-text p, .findings-text li, .findings-text span {
    font-size: 0.82rem !important;
    line-height: 1.6 !important;
    color: #333333 !important;
    font-family: 'Space Mono', monospace !important;
}
.findings-text h1, .findings-text h2, .findings-text h3,
.findings-text h4, .findings-text h5, .findings-text h6 {
    font-size: 0.85rem !important;
    font-family: 'Anton', sans-serif !important;
    color: #111111 !important;
    background: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    text-shadow: none !important;
    margin: 0.5rem 0 0.25rem 0 !important;
    border-bottom: 1px solid #ddd;
}
.findings-text a { color: var(--accent-color) !important; }

/* ============================================
   HITL GATE — REVIEW MODE
   ============================================ */
.hitl-banner {
    background-color: var(--accent-color);
    border: var(--border-width) solid var(--border-color);
    box-shadow: var(--shadow-offset) var(--shadow-offset) 0px var(--border-color);
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.hitl-banner-icon {
    font-family: 'Anton', sans-serif;
    font-size: 1.2rem;
    letter-spacing: 3px;
    color: #ffffff !important;
    border: 2px solid rgba(255,255,255,0.6);
    padding: 0.3rem 0.7rem;
    flex-shrink: 0;
    white-space: nowrap;
}
.hitl-banner-text h3 {
    font-family: 'Anton', sans-serif !important;
    font-size: 1.5rem !important;
    color: #ffffff !important;
    background: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    letter-spacing: 2px;
}
.hitl-banner-text p {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.85) !important;
    margin: 0.2rem 0 0 0;
}
.hitl-panel {
    background: #ffffff;
    border: var(--border-width) solid var(--border-color);
    box-shadow: 4px 4px 0px var(--border-color);
    padding: 1rem;
    height: 100%;
}
.hitl-panel-label {
    font-family: 'Anton', sans-serif !important;
    font-size: 0.8rem !important;
    letter-spacing: 2px;
    color: #666 !important;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    display: block;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.3rem;
}

/* ============================================
   FINAL REPORT — STRUCTURED SECTIONS
   ============================================ */
.report-wrapper {
    border: var(--border-width) solid var(--border-color);
    box-shadow: var(--shadow-offset) var(--shadow-offset) 0px var(--border-color);
    overflow: hidden;
    margin-bottom: 2rem;
}
.report-title-bar {
    background-color: var(--border-color);
    padding: 0.75rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.report-title-bar span {
    font-family: 'Anton', sans-serif !important;
    color: #ffffff !important;
    font-size: 1.2rem;
    letter-spacing: 3px;
}
.report-section {
    padding: 1.2rem 1.5rem;
    border-bottom: 2px solid var(--border-color);
    background: #ffffff;
}
.report-section:last-child { border-bottom: none; }
.report-section-label {
    font-family: 'Anton', sans-serif !important;
    font-size: 0.7rem !important;
    letter-spacing: 3px;
    color: #888 !important;
    text-transform: uppercase;
    display: block;
    margin-bottom: 0.5rem;
}
.report-key-takeaway {
    background-color: var(--border-color) !important;
    padding: 1.2rem 1.5rem;
    border-bottom: 2px solid var(--border-color);
}
.report-key-takeaway .report-section-label { color: rgba(255,255,255,0.6) !important; }
.report-key-takeaway p, .report-key-takeaway div {
    color: #ffffff !important;
    font-size: 1.1rem !important;
    font-weight: bold;
    line-height: 1.5;
}
.report-bottom-line {
    background-color: var(--accent-color) !important;
    padding: 1.2rem 1.5rem;
}
.report-bottom-line .report-section-label { color: rgba(255,255,255,0.7) !important; }
.report-bottom-line p, .report-bottom-line div {
    color: #ffffff !important;
    font-weight: bold;
}
.report-analysis {
    border-left: 6px solid var(--accent-color) !important;
    background: #fafafa !important;
}

</style>
""", unsafe_allow_html=True)
