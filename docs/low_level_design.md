# Low Level Design - Polyagentic Research Assistant

## 1. State Schema

All agents read from and write to a single shared `ResearchState` dictionary. LangGraph manages state transitions automatically.

```python
class ResearchState(TypedDict):
    main_task: str                                    # User's research topic
    research_findings: Annotated[List[str], operator.add]  # Append-only list of research summaries
    draft: str                                        # Current report draft (overwritten each revision)
    critique_notes: str                               # Latest critique output
    revision_number: int                              # Tracks revision count (0-indexed)
    next_step: str                                    # Routing signal: "researcher" | "writer" | "END"
    current_sub_task: str                             # Supervisor's task description for the current step
    llm_provider: str                                 # "groq" or "ollama"
    llm_model: str                                    # Model identifier string
    ollama_url: str                                   # Ollama host URL (only used when provider=ollama)
```

## 2. Graph Topology

```
Entry ──► supervisor ──┬──► researcher ──► supervisor (loop back)
                       ├──► writer ──► critiquer ──► supervisor (loop back)
                       └──► END
```

### Edge Definitions

| From | To | Type | Condition |
|------|----|------|-----------|
| `supervisor` | `researcher` | Conditional | `state["next_step"] == "researcher"` |
| `supervisor` | `writer` | Conditional | `state["next_step"] == "writer"` |
| `supervisor` | `END` | Conditional | `state["next_step"] == "END"` |
| `researcher` | `supervisor` | Static | Always |
| `writer` | `critiquer` | Static | Always |
| `critiquer` | `supervisor` | Static | Always |

## 3. Agent Internals

### 3.1 Supervisor (`create_supervisor_chain`)

Decision priority (evaluated top-to-bottom, first match wins):

| # | Condition | Route | Rationale |
|---|-----------|-------|-----------|
| 1 | `"APPROVED" in critique` and draft exists | `END` | Work is done |
| 2 | No research findings | `researcher` | Need data first |
| 3 | Has research, no draft | `writer` | Ready to write |
| 4 | Has draft, no critique | `writer` | Triggers write → critique chain |
| 5 | Has critique (not approved), revision < 3 | `writer` | Needs revision |
| 6 | revision >= 3 | `END` | Force stop |
| 7 | LLM fallback | Parsed from JSON response | Last resort |
| 8 | Final fallback | `writer` | Default safe route |

### 3.2 Researcher (`create_researcher_agent`)

```
Input: sub_task string from state
  │
  ├─► Tavily Search API (max 5 results, basic depth)
  │     Returns: list of {title, url, content}
  │
  ├─► Format top 3 results into markdown snippets
  │
  └─► LLM summarization prompt
        "Provide 5-7 bullet points of key findings"
        │
        └─► Output appended to state["research_findings"]
```

**Error handling**: If Tavily or LLM fails, returns a generic string rather than crashing.

### 3.3 Writer (`create_writer_chain`)

- **First draft**: Uses `research_findings` to write a structured report (Intro, Findings, Analysis, Conclusion).
- **Revision**: Uses existing `draft` + `critique_notes` to address feedback.
- Increments `revision_number` after each invocation.

### 3.4 Critiquer (`create_critique_chain`)

- Evaluates draft on 5 axes: completeness, accuracy, structure, clarity, depth.
- **Short-circuits**:
  - Draft < 100 chars → auto-approve (nothing meaningful to critique).
  - revision >= 3 → auto-approve (prevent infinite loops).
- Outputs either `"APPROVED - ..."` or actionable revision feedback.

## 4. Dynamic LLM Provider (`_get_llm`)

```
_get_llm(state_or_dict)
  │
  ├─ state is None or not dict ──► return default global `llm` (Groq)
  │
  ├─ provider == "ollama" ──► ChatOllama(model, base_url)
  │     On failure ──► fallback to default `llm`
  │
  └─ provider == "groq" (or anything else) ──► ChatGroq(model, api_key)
        On failure ──► fallback to default `llm`
```

Every agent calls `_get_llm(state)` before each LLM invocation, so provider switching is per-run (not per-session).

## 5. File Structure

```
polyagentic-research-assistant/
├── app.py                 # Streamlit UI and graph streaming
├── graph.py               # LangGraph state machine definition
├── agents.py              # Agent factory functions and LLM helpers
├── prompts.py             # All prompt templates
├── main.py                # Placeholder CLI entry point
├── visualize_graph.py     # Graph diagram export utility
├── requirements.txt       # pip dependencies
├── pyproject.toml         # Project metadata and uv config
├── .env                   # API keys (gitignored)
├── .env.example           # Template for .env
├── tests/
│   └── test_tools.py      # Unit tests
├── assets/                # Generated graph images
├── context/               # Internal task tracking (gitignored)
└── docs/                  # Design documentation
```
