# High Level Design - Polyagentic Research Assistant

## 1. Overview

A multi-agent research assistant that takes a topic from the user and produces a polished research report. Four specialized AI agents collaborate in a supervised loop — researching the web, writing drafts, critiquing quality, and coordinating the workflow — until the report meets quality standards or a revision cap is reached.

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit UI (app.py)               │
│  Topic Input ─► Live Agent Log ─► Final Report       │
└──────────────────────┬──────────────────────────────┘
                       │  streams graph events
                       ▼
┌─────────────────────────────────────────────────────┐
│              LangGraph State Machine (graph.py)      │
│                                                      │
│   ┌────────────┐     ┌────────────┐                  │
│   │ Supervisor │────►│ Researcher │──┐               │
│   │  (router)  │     │  (search)  │  │               │
│   └─────┬──────┘◄────┘            │  │               │
│         │                         │  │               │
│         │    ┌────────────┐       │  │               │
│         └───►│   Writer   │───────┘  │               │
│              │  (draft)   │          │               │
│              └─────┬──────┘          │               │
│                    │                 │               │
│              ┌─────▼──────┐         │               │
│              │  Critiquer │─────────┘               │
│              │  (review)  │                          │
│              └────────────┘                          │
└─────────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Groq API    Ollama (local)  Tavily Search
      (cloud)      (self-host)    (web search)
```

## 3. Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **UI Layer** | `app.py` | Streamlit interface — topic input, sidebar config, live agent log, report display, download |
| **Graph Engine** | `graph.py` | Defines `ResearchState`, wires nodes and edges, compiles the LangGraph state machine |
| **Agent Logic** | `agents.py` | Factory functions for each agent, dynamic LLM provider selection (`_get_llm`), Tavily search integration |
| **Prompts** | `prompts.py` | All prompt templates for supervisor, researcher, writer, and critiquer |
| **Tests** | `tests/test_tools.py` | Unit tests for LLM compatibility helper and dynamic provider selection |

## 4. Workflow (Happy Path)

1. User enters a research topic in the Streamlit UI.
2. Supervisor routes to **Researcher** (no findings exist yet).
3. Researcher queries Tavily Search, LLM summarizes results into bullet points.
4. Supervisor routes to **Writer** (findings exist, no draft yet).
5. Writer synthesizes research into a structured Markdown report.
6. **Critiquer** evaluates the draft — either approves or requests revisions.
7. If revisions needed, Supervisor sends back to Writer (max 3 revisions).
8. On approval or max revisions, Supervisor routes to **END**.
9. Streamlit displays the final report with stats and a download button.

## 5. Key Design Decisions

- **Deterministic routing first, LLM fallback second**: The Supervisor uses hardcoded rules (lines 122–170 in `agents.py`) before ever calling the LLM. This prevents the workflow from getting stuck due to LLM parsing failures.
- **Dual LLM support**: Users can switch between Groq (cloud) and Ollama (local) at runtime via the sidebar. The `_get_llm()` factory handles instantiation.
- **Append-only research**: `research_findings` uses `Annotated[List[str], operator.add]` so findings accumulate across research cycles rather than being overwritten.
- **Revision cap**: Hard limit of 3 revisions prevents infinite critique loops.

## 6. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Orchestration | LangGraph (StateGraph) |
| LLM Framework | LangChain |
| Cloud LLM | Groq (llama-3.3-70b, mixtral, gemma2) |
| Local LLM | Ollama (any pulled model) |
| Web Search | Tavily Search API |
| Package Mgmt | uv |
| Testing | pytest |
