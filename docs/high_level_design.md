# High-Level Design — Polyagentic Research Assistant

## 1. Overview

A multi-agent research assistant that takes a topic and produces a polished, sourced report. Four specialized agents collaborate in a supervised loop — researching the web, writing drafts, critiquing quality, and coordinating the workflow — until the report meets quality standards or a revision cap is reached. A single **Human-in-the-Loop (HITL) checkpoint** after the research phase lets the user review, edit, or redirect findings before any writing begins.

The system is two independently-runnable services:

- **`backend/`** — FastAPI + LangGraph. Owns the agent runtime, LLM/search calls, and the graph's own checkpointed state.
- **`frontend/`** — Next.js. Owns the UI and a small persistence layer (saved report history via Prisma). The browser only ever talks to Next.js; Next.js's Route Handlers are the sole path to the backend.

They ship together as one Docker image for deployment (see `docs/low_level_design.md` §6), but are architecturally decoupled — the backend has no knowledge of Next.js, and could serve any other client (a CLI, a different frontend, another service) unchanged.

## 2. Architecture

```
┌───────────────────────────────────────────────────────────┐
│                     Browser (React UI)                     │
└───────────────────────────┬─────────────────────────────────┘
                             │ fetch / SSE
┌───────────────────────────▼─────────────────────────────────┐
│                  Next.js — Route Handlers                   │
│   /api/research/stream        → proxies to FastAPI (SSE)    │
│   /api/research/[id]/resume   → proxies to FastAPI (SSE)    │
│   /api/research/[id]/state    → proxies to FastAPI          │
│   /api/reports                → Prisma (saved report history)│
│   /api/health                 → proxies to FastAPI /health  │
└───────────────────────────┬─────────────────────────────────┘
                             │ HTTP, server-side only
┌───────────────────────────▼─────────────────────────────────┐
│                  FastAPI — LangGraph runtime                │
│                                                               │
│   ┌────────────┐     ┌────────────┐                         │
│   │ Supervisor │────►│ Researcher │                         │
│   │  (router)  │     │  (search)  │                         │
│   └─────┬──────┘     └─────┬──────┘                         │
│         │                  │                                │
│         │           ┌──────▼──────┐                          │
│         │           │  [HITL]     │                          │
│         │           │ interrupt() │◄── Command(resume=...)   │
│         │           └──────┬──────┘                          │
│         │◄─────────────────┘                                 │
│         │    ┌────────────┐                                  │
│         └───►│   Writer   │                                  │
│              └─────┬──────┘                                  │
│              ┌─────▼──────┐                                  │
│              │  Critiquer │──► supervisor (loop back)         │
│              └────────────┘                                  │
└───────────────────────────┬─────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
          Groq API    Ollama (local)   Tavily Search
```

## 3. Core Components

| Component | Location | Responsibility |
|-----------|----------|-----------------|
| **Frontend UI** | `frontend/src/app`, `frontend/src/components` | Topic input, live agent activity stream, HITL review panel, report view, saved-report history |
| **Frontend API layer** | `frontend/src/app/api/**/route.ts` | Zod-validated Route Handlers — proxy agent traffic to FastAPI, own the Prisma-backed report history directly |
| **Backend API** | `backend/app/main.py` | FastAPI app — SSE streaming endpoints, health check, lifespan-managed checkpointer |
| **Graph engine** | `backend/app/graph.py` | Defines `ResearchState`, wires nodes/edges, compiles the LangGraph `StateGraph` |
| **Agent logic** | `backend/app/agents.py` | Per-agent behavior, LLM/search client factories, retry policy, sub-query planning |
| **Structured schemas** | `backend/app/schemas.py` | Pydantic models for every LLM structured-output call and every API request/response |
| **Prompts** | `backend/app/prompts.py` | All prompt templates, including the untrusted-web-content delimiting used by the Researcher |

## 4. Workflow (Happy Path)

1. User enters a research topic in the UI.
2. Supervisor routes to **Researcher** (no findings exist yet).
3. Researcher plans 2-4 sub-queries, runs them concurrently against Tavily, dedupes results by URL, and asks the LLM to extract sourced bullets (structured output).
4. **[HITL] Research Review Gate** — the graph pauses via `interrupt()`. The UI shows the findings with three options:
   - **Approve** → accept findings as-is (or edited) and continue to Writer.
   - **Edit** → modify the findings text before continuing.
   - **Re-search** → type a refined query; Researcher runs again.
5. Supervisor routes to **Writer** (findings confirmed).
6. Writer synthesizes research into a structured Markdown report (`Key Takeaway → Findings → Analysis → Bottom Line`).
7. **Critiquer** evaluates the draft with a structured verdict — approve, or return up to 3 concrete fixes.
8. If revisions are needed, Supervisor sends back to Writer (max 3 revisions).
9. On approval or max revisions, Supervisor routes to `END`.
10. The UI shows the final report with stats, a download option, and an option to save it to history.

## 5. Key Design Decisions

See the README's "Key Design Decisions" section for the full list with rationale. Summarized:

- Deterministic routing first; structured-output LLM fallback second.
- Every control-flow-gating LLM call uses a typed Pydantic schema — no substring matching.
- Research is decomposed into concurrent sub-queries rather than one flat search.
- Retries with backoff on transient failures; auth failures fail fast.
- Node failures surface as typed errors, never fabricated success text.
- Checkpointing is persistent (`AsyncSqliteSaver`), not in-memory.
- Untrusted web content is explicitly delimited in prompts as a prompt-injection mitigation.
- HITL uses LangGraph's `interrupt()` idiom, not the older static `interrupt_before`.
- The Next.js/FastAPI boundary is typed via Zod + Pydantic kept in sync by hand — tRPC was deliberately not used, since it can't type-check across a language boundary (see README for the full rationale).

## 6. Tech Stack

See the README's "Tech Stack" table — kept in one place to avoid drift between documents.
