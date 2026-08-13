# Low-Level Design — Polyagentic Research Assistant

## 1. State Schema (`backend/app/graph.py`)

```python
class ResearchState(TypedDict):
    main_task: str
    research_findings: Annotated[List[dict], operator.add]  # list of ResearchBrief dicts
    draft: str
    critique_notes: str            # human-readable summary/fixes, for display + writer prompt
    critique_approved: bool        # structured verdict — the actual control-flow signal
    revision_number: int
    next_step: str
    current_sub_task: str
    llm_provider: str              # "groq" | "ollama"
    llm_model: str
    ollama_url: str
    hitl_approved: bool
    hitl_edited_findings: str
    error: str                     # set by a node on failure; never both this and its normal fields
```

`research_findings` entries are plain dicts (not live Pydantic instances) so they stay trivially JSON-serializable for both the SQLite checkpointer and the SSE stream to the frontend. The `ResearchBrief` Pydantic model in `schemas.py` is used only at construction time (`.model_dump()`), never persisted as a typed object in state.

## 2. Graph Topology

```
Entry ──► supervisor ──┬──► researcher ──► human_review ──┬──► supervisor (approve/edit)
                        │                                  └──► researcher (re-search)
                        ├──► writer ──► critiquer ──► supervisor (loop back)
                        └──► END
```

| From | To | Type | Condition |
|------|----|------|-----------|
| `supervisor` | `researcher` / `writer` / `END` | Conditional | `_route_after_supervisor(state)` on `state["next_step"]` |
| `researcher` | `human_review` | Static | Always |
| `human_review` | `supervisor` / `researcher` | Conditional | `_route_after_human_review(state)` on `state["next_step"]` |
| `writer` | `critiquer` | Static | Always |
| `critiquer` | `supervisor` | Static | Always |

## 3. Agent Internals

### 3.1 Supervisor (`create_supervisor_chain`, `agents.py`)

Decision priority (first match wins):

| # | Condition | Route |
|---|-----------|-------|
| 1 | `critique_approved` and draft exists | `END` |
| 2 | No research findings | `researcher` |
| 3 | Has research, no draft | `writer` |
| 4 | Has draft, no critique yet | `writer` |
| 5 | Has critique, not approved, `revision_number < max_revisions` | `writer` |
| 6 | `revision_number >= max_revisions` | `END` |
| 7 | None of the above (ambiguous) | LLM fallback — `llm.with_structured_output(SupervisorDecision)` |

The fallback is rarely reached in practice; it exists so a malformed or unexpected state still produces a valid route instead of the graph stalling.

### 3.2 Researcher (`create_researcher_agent`, `agents.py`)

```
topic (from current_sub_task, falling back to main_task)
  │
  ├─► _plan_sub_queries(llm, topic)
  │     llm.with_structured_output(SubQueryPlan) → 2-4 focused, non-overlapping queries
  │     (falls back to [topic] if planning fails — never blocks research entirely)
  │
  ├─► asyncio.gather(*[_search_one(q) for q in sub_queries])
  │     Each hits Tavily concurrently via TavilySearch.ainvoke
  │     Raises SearchProviderError if *all* sub-queries fail; partial failures are logged
  │     and the surviving results are used
  │
  ├─► _dedupe_results — merge by URL, cap at 8 sources
  │
  └─► llm.with_structured_output(ResearchBullets) over the merged, delimited results
        → { bullets: [...], sources: [{title, url}, ...] } stored as one ResearchBrief
```

**Error handling**: a total search failure raises `SearchProviderError`, which `research_node` catches and turns into `{"error": "..."}` — never a fabricated "research completed" placeholder. A *summarization* failure (LLM call after search succeeded) degrades gracefully to using raw search snippets as bullets, since real search results are still better than nothing.

### 3.3 Human Review Node (`human_review_node`, `graph.py`)

Uses LangGraph's `interrupt()` function directly inside the node body — the modern idiom, replacing the older `interrupt_before=[...]` static compile-time list:

```python
async def human_review_node(state):
    decision = interrupt({"type": "research_review", "latest_finding": ...})
    # execution pauses here; the checkpointer persists state to disk
    # decision is whatever the client later sends via Command(resume=decision)
    if decision.get("action") == "research":
        return {"current_sub_task": decision["query"], "next_step": "researcher"}
    return {"hitl_approved": True, "hitl_edited_findings": decision.get("edited_text", ""), "next_step": "supervisor"}
```

Resuming (`backend/app/main.py`, `POST /api/research/{thread_id}/resume`) calls `graph.astream(Command(resume=resume_payload), config)`. Because the checkpointer is `AsyncSqliteSaver`, the pause survives a backend process restart — the frontend can reconnect and resume hours later against the same `thread_id`.

### 3.4 Writer (`create_writer_chain`, `agents.py`)

- First draft: uses `hitl_edited_findings` if the user edited at the review gate, otherwise the accumulated `research_findings`, rendered from structured dicts back into prompt-friendly Markdown by `_format_research_for_prompt`.
- Revision: uses the existing `draft` + `critique_notes`.
- Raises `LLMProviderError` on an empty response rather than silently returning `"Draft in progress..."`.
- Increments `revision_number` on every call (`write_node` in `graph.py`), first draft or revision alike.

### 3.5 Critiquer (`create_critique_chain`, `agents.py`)

- Short-circuits: draft under 100 chars → auto-reject with a fix instruction; `revision_number >= max_revisions` → auto-approve (prevents infinite loops even if the LLM is stubborn).
- Otherwise calls `llm.with_structured_output(CritiqueVerdict)` — `{approved: bool, summary: str, fixes: list[str]}` (max 3 fixes).
- `critique_node` derives `critique_notes` (a display string) from the structured verdict, but `critique_approved` — the actual field the Supervisor's routing rules read — comes straight from `verdict.approved`. Nothing downstream substring-matches report text for the word "approved".

## 4. LLM / Search Client Factory (`agents.py`)

```
_get_llm(state_or_dict)
  │
  ├─ provider == "ollama" ──► ChatOllama(model, base_url, timeout)
  │     On init failure ──► raises LLMProviderError (never silently substitutes Groq)
  │
  └─ provider == "groq" (default) ──► ChatGroq(model, api_key, timeout)
        No GROQ_API_KEY configured ──► raises LLMProviderError immediately
```

Built fresh per call from request state — there is no module-level singleton LLM client, so a misconfigured provider can't leak into a request that asked for the other one. `_tavily_tool()` is similarly lazy and raises `SearchProviderError` if `TAVILY_API_KEY` is missing, rather than prompting on stdin at import time (a real bug in the original single-service version: `getpass.getpass()` at module import would hang a headless container with no TTY).

Every `_invoke` / `_invoke_structured` call is wrapped in a `tenacity` retry: up to `LLM_MAX_RETRIES` attempts with exponential backoff, retried only when `_is_transient()` returns true (HTTP 408/429/5xx, connection/timeout errors) — an auth error (401) fails on the first attempt.

## 5. FastAPI Layer (`backend/app/main.py`)

| Endpoint | Method | Behavior |
|----------|--------|----------|
| `/health` | GET | Reports whether Tavily/Groq are configured and whether Ollama is reachable |
| `/api/research/stream` | POST | Starts a new run (`StartResearchRequest`), streams SSE events until completion or the HITL interrupt |
| `/api/research/{thread_id}/resume` | POST | Sends `Command(resume=...)` from a `ResumeAction`, streams SSE events onward |
| `/api/research/{thread_id}/state` | GET | Returns the current checkpointed state snapshot (404 if unknown) |

SSE event shape (`_sse` / `_stream_events` in `main.py`):

```
event: thread      data: {"thread_id": "..."}
event: step        data: {"node": "researcher", "output": {...}}
event: node_error  data: {"node": "writer", "error": "..."}
event: interrupt   data: {"payload": {"type": "research_review", "latest_finding": {...}}}
event: done        data: {"final_state": {...}}
```

The checkpointer (`AsyncSqliteSaver`) is opened once in the FastAPI `lifespan` context manager and stored on `app.state.graph` — not rebuilt per-request.

## 6. Deployment Topology

Single Docker image, two processes, one exposed port — see the root `Dockerfile` and `docker/start.sh`:

1. **Build stage** (`node:20-bookworm-slim`): installs frontend deps (including `better-sqlite3`'s native addon, which needs `python3 make g++` at install time), runs `prisma generate` and `prisma migrate deploy` against a build-time seed database, then `next build` with `output: "standalone"`.
2. **Final stage** (`python:3.11-slim` + Node.js installed alongside): installs backend deps via `pip install -r requirements.txt`, copies the Next.js standalone output, static assets, and the seeded Prisma database template.
3. **`docker/start.sh`**: on first boot, copies the seed database into `/data/app.db` if one doesn't already exist there; sets `DATABASE_URL` and `CHECKPOINT_DB_PATH` to point into `/data`; starts `uvicorn` bound to `127.0.0.1:8000` and `node server.js` bound to `0.0.0.0:$PORT` (default `7860`, Hugging Face Spaces' expected port); traps and propagates a failure in either process to stop the container.

Because `BACKEND_URL` defaults to `http://127.0.0.1:8000`, FastAPI is never exposed outside the container — the only public surface is the Next.js server.
