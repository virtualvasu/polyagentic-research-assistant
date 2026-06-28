# Polyagentic Research Assistant

A **stateful multi-agent system** that takes a research topic and produces a structured, sourced report — autonomously. Four specialized AI agents collaborate in a supervised loop, with a **Human-in-the-Loop checkpoint** at the research boundary so you control what goes into the report before writing begins.

> Built with LangGraph · LangChain · Groq · Ollama · Tavily · Streamlit

---

## How it works

```
User Input
    │
    ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Supervisor │────►│  Researcher  │────►│  [ YOU REVIEW ]  │
│  (router)   │     │  web search  │     │  edit / approve  │
└──────┬──────┘     └──────────────┘     └────────┬─────────┘
       │                                           │
       │◄──────────────────────────────────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Writer    │────►│  Critiquer   │──► loop (max 3 revisions) ──► Final Report
│  (drafter)  │     │  (editor)    │
└─────────────┘     └──────────────┘
```

### The 5 agents

| Agent | Role |
|-------|------|
| **Supervisor** | Deterministic router — decides who acts next based on workflow state. Falls back to LLM only when logic is ambiguous. |
| **Researcher** | Queries Tavily Search, then uses the LLM to distill results into 5 sourced bullet points. |
| **[HITL] Review Gate** | Pauses the graph. You see the findings, edit them, or trigger a re-search before any writing happens. |
| **Writer** | Synthesizes confirmed findings into a 400–600 word structured report (`Key Takeaway → Findings → Analysis → Bottom Line`). Revises on critique. |
| **Critiquer** | Senior editor — checks source fidelity, structure, and substance. Approves at 80% quality. Returns max 3 concrete, actionable fixes. |

---

## Key design decisions

**Deterministic routing first, LLM fallback second** — The Supervisor uses hardcoded state-based rules before ever calling the LLM. This prevents the workflow from getting stuck on JSON parsing failures or hallucinated route decisions.

**Single HITL gate at the research boundary** — There is exactly one human checkpoint: after research, before writing. This is the highest-leverage intervention point. Bad source material contaminates every downstream step; one 10-second review prevents wasted revision cycles.

**Append-only research findings** — `research_findings` uses `Annotated[List[str], operator.add]`, so findings accumulate across multiple research cycles rather than being overwritten. Re-searching adds to the pool.

**Hard revision cap** — Maximum 3 critique → writer cycles. The Critiquer prompt is designed to approve at 80% quality, making the automated loop reliable enough to run without further human intervention.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) — `StateGraph` with `MemorySaver` checkpointing |
| LLM Framework | [LangChain](https://python.langchain.com/) |
| Cloud LLM | [Groq](https://groq.com/) — `llama-3.3-70b-versatile`, `mixtral-8x7b`, `gemma2-9b` |
| Local LLM | [Ollama](https://ollama.com/) — any locally pulled model |
| Web Search | [Tavily Search API](https://tavily.com/) |
| Frontend | [Streamlit](https://streamlit.io/) with custom Brutalist CSS design system |
| Package Management | [uv](https://docs.astral.sh/uv/) |
| Testing | pytest |

---

## Project structure

```
polyagentic-research-assistant/
├── app.py                  # Streamlit entry point — state machine runner
├── graph.py                # LangGraph StateGraph — nodes, edges, compilation
├── agents.py               # Agent factory functions + dynamic LLM provider
├── prompts.py              # All prompt templates (supervisor, writer, critiquer)
├── ui/
│   ├── style.py            # Brutalist CSS design system (injected via st.markdown)
│   ├── sidebar.py          # Sidebar config — provider, model, iterations
│   ├── state.py            # Session state init + API key validation
│   └── stream_handler.py   # Live agent activity log + pipeline header renderer
├── tests/
│   ├── test_agents.py      # Unit tests for agent chains and LLM factory
│   └── test_graph.py       # Unit tests for graph routing logic
├── docs/
│   ├── high_level_design.md
│   └── low_level_design.md
├── .env.example
└── requirements.txt
```

---

## Setup

### Prerequisites
- Python 3.10+
- A [Groq API key](https://console.groq.com/) (free)
- A [Tavily API key](https://tavily.com/) (free tier available)
- (Optional) [Ollama](https://ollama.com/) running locally for local inference

### Install

```bash
# Clone the repo
git clone https://github.com/virtualvasu/polyagentic-research-assistant.git
cd polyagentic-research-assistant

# Install dependencies (recommended: uv)
pip install uv
uv pip install -r requirements.txt

# Or with standard pip
pip install -r requirements.txt
```

### Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here

# Optional — for Ollama local models
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=llama3.1:latest,llama3.1:8b,qwen2.5:7b
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Using Ollama (local inference)

Pull a model:
```bash
ollama pull llama3.1:latest
```

In the Streamlit sidebar, switch **LLM Provider** to `Ollama` and select your model. The Groq API key is not required in Ollama mode (Tavily key still is).

---

## Running tests

```bash
pytest tests/ -v
```

---

## Workflow walkthrough

1. Enter a research topic (e.g., *"Impact of quantum computing on post-quantum cryptography"*)
2. The **Supervisor** routes to the **Researcher**
3. Researcher queries Tavily, LLM condenses results into 5 sourced bullet points
4. **You are shown the findings** — you can approve, edit inline, or trigger a re-search with a new query
5. After approval, **Supervisor** routes to **Writer**
6. Writer produces a structured report: `Key Takeaway → Findings → Analysis → Bottom Line`
7. **Critiquer** reviews — either approves or returns up to 3 concrete fixes
8. Writer revises; loop repeats up to 3 times
9. Final report is displayed with word count, revision count, and a download button

---

## Configuration reference

| Sidebar Setting | Default | Description |
|----------------|---------|-------------|
| Max Iterations | 15 | LangGraph recursion limit — prevents infinite loops |
| LLM Provider | Groq | Switch between Groq (cloud) and Ollama (local) |
| Model Name | llama-3.3-70b-versatile | Model used for all agent chains |
| Ollama Host URL | http://localhost:11434 | Only shown when Ollama is selected |

---

## License

MIT
