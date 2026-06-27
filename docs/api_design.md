# API Design - Polyagentic Research Assistant

> This project does not expose a REST/HTTP API. It runs as a local Streamlit application.
> This document covers the **internal Python interfaces** — the public functions and data contracts between modules.

## 1. Graph API (`graph.py`)

### `app` (compiled LangGraph)

The primary entry point. A compiled `StateGraph` instance.

```python
from graph import app

# Execute the full workflow (streaming)
for step in app.stream(initial_state, config=config):
    node_name = list(step.keys())[0]
    node_output = step[node_name]
```

**Input — `initial_state`**:

```python
{
    "main_task": str,           # Required. The research topic.
    "research_findings": [],    # Required. Start empty.
    "draft": "",                # Required. Start empty.
    "critique_notes": "",       # Required. Start empty.
    "revision_number": 0,       # Required. Start at 0.
    "next_step": "",            # Required. Start empty.
    "current_sub_task": "",     # Required. Start empty.
    "llm_provider": str,        # Required. "groq" or "ollama".
    "llm_model": str,           # Required. Model name string.
    "ollama_url": str            # Optional. Ollama host URL.
}
```

**Config**:

```python
{"recursion_limit": int}  # Max number of graph steps (default: 15)
```

**Output (per stream step)**:

Each yielded `step` is a dict with a single key (the node name) mapping to that node's output dict.

```python
# Example stream outputs:
{"supervisor": {"next_step": "researcher", "current_sub_task": "..."}}
{"researcher": {"research_findings": ["..."]}}
{"writer":     {"draft": "...", "revision_number": 1}}
{"critiquer":  {"critique_notes": "APPROVED - ...", "next_step": "END"}}
```

---

## 2. Agent Factory API (`agents.py`)

### `create_supervisor_chain() → Callable[[ResearchState], dict]`

Returns a function that takes the full state and returns a routing decision.

```python
# Return format:
{"next_step": "researcher" | "writer" | "END", "task_description": str}
```

---

### `create_researcher_agent() → Callable[[dict], dict]`

Returns a function that takes an input dict and returns research output.

```python
# Input:
{"input": str, "llm_provider": str, "llm_model": str, "ollama_url": str}

# Return:
{"output": str, "input": str}
```

---

### `create_writer_chain() → Callable[[ResearchState], str]`

Returns a function that takes the full state and returns the draft text as a string.

---

### `create_critique_chain() → Callable[[ResearchState], str]`

Returns a function that takes the full state and returns critique text.
Contains `"APPROVED"` if the draft passes review.

---

### `_get_llm(state_or_dict) → LLM instance`

Dynamic LLM factory. Returns a `ChatGroq` or `ChatOllama` instance based on state config.

```python
# Falls back to default global Groq LLM if:
#   - input is None / not a dict
#   - llm_provider key is missing
#   - instantiation fails
```

---

### `_call_llm(llm_obj, *args, **kwargs) → response`

Compatibility adapter. Tries `invoke()` → `run()` → `__call__()` in order.

---

## 3. Streamlit Interface (`app.py`)

### Sidebar Controls

| Control | Type | Values | Default |
|---------|------|--------|---------|
| Max Workflow Iterations | Slider | 5–25 | 15 |
| LLM Provider | Selectbox | Groq, Ollama | Groq |
| Model Name (Groq) | Selectbox | llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it | llama-3.3-70b-versatile |
| Model Name (Ollama) | Text Input | any string | llama3.3 |
| Ollama Host URL | Text Input | any URL | http://localhost:11434 |

### `check_api_keys(provider: str) → bool`

Validates environment variables. Checks `TAVILY_API_KEY` always, checks `GROQ_API_KEY` only when `provider == "groq"`.

---

## 4. Environment Variables

| Variable | Required | Used By |
|----------|----------|---------|
| `TAVILY_API_KEY` | Always | Researcher agent (web search) |
| `GROQ_API_KEY` | When provider = groq | All agents (LLM calls) |
