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
    # --- HITL fields (planned) ---
    hitl_approved: bool                               # True once user confirms research at the Review Gate
    hitl_edited_findings: str                         # User-edited findings text (if user chose Edit mode)
```

## 2. Graph Topology

**Current (no HITL):**
```
Entry ──► supervisor ──┬──► researcher ──► supervisor (loop back)
                       ├──► writer ──► critiquer ──► supervisor (loop back)
                       └──► END
```

**Planned (with HITL Research Review Gate):**
```
Entry ──► supervisor ──┬──► researcher ──► human_review ──┬──► supervisor (proceed/edit)
                       │                                  └──► researcher (re-search)
                       ├──► writer ──► critiquer ──► supervisor (loop back)
                       └──► END
```

### Edge Definitions (Planned)

| From | To | Type | Condition |
|------|----|------|-----------|
| `supervisor` | `researcher` | Conditional | `state["next_step"] == "researcher"` |
| `supervisor` | `writer` | Conditional | `state["next_step"] == "writer"` |
| `supervisor` | `END` | Conditional | `state["next_step"] == "END"` |
| `researcher` | `human_review` | Static | Always (replaces direct → supervisor) |
| `human_review` | `supervisor` | Conditional | User chose Proceed or Edit |
| `human_review` | `researcher` | Conditional | User chose Re-search |
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
        "Extract exactly 5 factual bullet points with source attribution"
        Rules: 1-2 sentences per bullet, quantitative facts prioritised,
               no filler phrases, no invented content
        │
        └─► Output appended to state["research_findings"]
```

**Error handling**: If Tavily or LLM fails, returns a generic string rather than crashing.

### 3.3 Human Review Node (`human_review_node`) — Planned

This node is a **LangGraph interrupt node**. It does not call any LLM. It pauses the graph and hands control back to Streamlit.

```
researcher completes
  │
  └─► human_review_node
        │
        │  [Graph paused — LangGraph MemorySaver checkpoints state]
        │
        Streamlit renders:
          - The 5 bullet points from research_findings
          - 3 action buttons:
              [Proceed]    → sets hitl_approved=True, next_step="writer"
              [Edit]       → shows text area; user edits findings;
                             sets hitl_edited_findings, hitl_approved=True
              [Re-search]  → shows query input; user types new query;
                             sets next_step="researcher", new current_sub_task
        │
        Graph resumes with updated state
```

**LangGraph mechanics:**
- `workflow.compile(interrupt_before=["human_review"])` pauses before the node.
- `MemorySaver` checkpointer persists state between the pause and resume.
- `app.invoke(Command(resume=user_decision), config=config)` resumes execution.

### 3.5 Writer (`create_writer_chain`)

- **First draft**: Uses confirmed `research_findings` (or `hitl_edited_findings` if user edited) to write a structured report using the template: Key Takeaway → Findings → Analysis → Bottom Line.
- **Revision**: Uses existing `draft` + `critique_notes` to address feedback.
- Target length: 400–600 words. Filler phrases explicitly banned by prompt.
- Increments `revision_number` after each invocation.

### 3.6 Critiquer (`create_critique_chain`)

- Evaluates draft on 4 axes: answers the question, claims are grounded, free of filler, logical structure.
- **Short-circuits**:
  - Draft < 100 chars → auto-approve.
  - revision >= 3 → auto-approve (prevent infinite loops).
- Outputs either `"APPROVED - ..."` or a numbered list of **max 3** concrete `Problem / Fix` items.
- Rule: approve at 80% quality — does not nitpick style or grammar.

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

## 6. HITL Implementation Plan (Planned)

Changes required to implement the Research Review Gate:

| File | Change |
|------|--------|
| `graph.py` | Add `human_review_node` function; add node to workflow; change `researcher → supervisor` static edge to `researcher → human_review`; add conditional edges out of `human_review`; compile with `interrupt_before=["human_review"]` and `MemorySaver` |
| `graph.py` | Add `hitl_approved: bool` and `hitl_edited_findings: str` to `ResearchState` |
| `app.py` | Replace single `app.stream()` loop with a two-phase execution model: Phase 1 streams until the interrupt; Phase 2 renders the Review Gate UI (bullets + 3 buttons); Phase 3 resumes graph with `app.invoke(Command(resume=...))` |
| `pyproject.toml` | No new dependencies — `langgraph` already supports `MemorySaver` and `interrupt_before` |
