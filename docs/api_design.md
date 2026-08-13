# API Design — Polyagentic Research Assistant

Two API surfaces exist. The **FastAPI backend** is the real agent API — it's a standalone HTTP service any client could use, and its interactive docs are auto-generated at `/docs` (Swagger UI) and `/redoc`. The **Next.js Route Handlers** are a thin, Zod-validated proxy layer the browser actually talks to; they exist so the backend never faces the internet directly and so saved-report history (Prisma) has a natural home.

## 1. FastAPI Backend (`backend/app/main.py`)

Base URL: `http://127.0.0.1:8000` (internal-only in the combined Docker deployment).

### `GET /health`

```json
{ "tavily_configured": true, "groq_configured": true, "ollama_reachable": false }
```

### `POST /api/research/stream`

Starts a new run and streams Server-Sent Events until the run pauses at the HITL gate or completes.

**Request body** (`StartResearchRequest`):

```json
{ "topic": "Impact of quantum computing on cryptography", "llm_provider": "groq", "llm_model": "llama-3.3-70b-versatile" }
```

**Response**: `text/event-stream`. Event types:

| Event | Payload | Meaning |
|-------|---------|---------|
| `thread` | `{"thread_id": "..."}` | Emitted first — the ID needed for `/resume` and `/state` |
| `step` | `{"node": "researcher", "output": {...state fields the node returned...}}` | One LangGraph node finished |
| `node_error` | `{"node": "writer", "error": "..."}` | A node failed; the run is still resumable from its last good checkpoint |
| `interrupt` | `{"payload": {"type": "research_review", "latest_finding": {...}}}` | Paused at the HITL gate, awaiting `/resume` |
| `done` | `{"final_state": {...full ResearchState...}}` | Run reached `END` |

### `POST /api/research/{thread_id}/resume`

Sends the human's decision back into the paused graph and streams onward — same event shape as above.

**Request body** (`ResumeAction`):

```json
{ "action": "approve", "edited_text": "...findings the user optionally edited..." }
```

or

```json
{ "action": "research", "query": "a refined search query" }
```

### `GET /api/research/{thread_id}/state`

Returns the current checkpointed snapshot without advancing the graph — used for reload/recovery.

```json
{ "values": {...ResearchState...}, "next": ["human_review"] }
```

`next` is empty once the run has completed.

## 2. Next.js Route Handlers (`frontend/src/app/api/**`)

All request/response bodies are validated with the Zod schemas in `frontend/src/lib/schemas.ts`, hand-kept in sync with the backend's Pydantic models (see the README for why this is hand-synced rather than generated across the language boundary).

| Route | Method | Behavior |
|-------|--------|----------|
| `/api/research/stream` | POST | Validates, forwards to FastAPI, pipes the SSE `ReadableStream` straight through |
| `/api/research/[threadId]/resume` | POST | Same, for resume |
| `/api/research/[threadId]/state` | GET | Forwards, returns JSON |
| `/api/health` | GET | Forwards FastAPI's `/health`, adds a `reachable` flag (`false` if the backend can't be reached at all, rather than erroring) |
| `/api/reports` | GET / POST | Lists / creates saved reports — talks to Prisma directly, no backend involvement |
| `/api/reports/[id]` | GET / DELETE | Fetch / delete one saved report |

The streaming proxy routes (`stream`, `resume`) do no buffering — `new Response(backendRes.body, {...})` forwards the backend's `ReadableStream` byte-for-byte, so latency between an agent step finishing and the browser seeing it is the network hop, not batching.
