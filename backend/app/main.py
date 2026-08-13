# app/main.py

import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse

from app.config import get_settings
from app.graph import build_graph
from app.schemas import HealthResponse, ResumeAction, StartResearchRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RECURSION_LIMIT = 25


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db_path = Path(settings.checkpoint_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        app.state.graph = build_graph(checkpointer=checkpointer)
        logger.info("Graph compiled, checkpoints persisted to %s", db_path)
        yield


app = FastAPI(title="Polyagentic Research Assistant API", version="2.0.0", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _config_for(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}


def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data, default=str)}


async def _stream_events(graph, graph_input, config: dict):
    """Turns a LangGraph astream into SSE events. Node failures return an
    `error` field in state (see graph.py) rather than raising, so a run stays
    resumable — the last good checkpoint is untouched."""
    async for step in graph.astream(graph_input, config=config):
        node_name = next(iter(step.keys()))
        payload = step[node_name]

        if node_name == "__interrupt__":
            interrupt_obj = payload[0]
            yield _sse("interrupt", {"payload": interrupt_obj.value})
            continue

        if isinstance(payload, dict) and payload.get("error"):
            yield _sse("node_error", {"node": node_name, "error": payload["error"]})
            continue

        yield _sse("step", {"node": node_name, "output": payload})

    state = await graph.aget_state(config)
    if not state.next:
        yield _sse("done", {"final_state": state.values})


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    ollama_reachable = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_reachable = r.status_code == 200
    except Exception:
        ollama_reachable = False

    return HealthResponse(
        tavily_configured=bool(settings.tavily_api_key),
        groq_configured=bool(settings.groq_api_key),
        ollama_reachable=ollama_reachable,
    )


@app.post("/api/research/stream")
async def start_research(req: StartResearchRequest, request: Request):
    thread_id = str(uuid.uuid4())
    initial_state = {
        "main_task": req.topic,
        "research_findings": [],
        "draft": "",
        "critique_notes": "",
        "critique_approved": False,
        "revision_number": 0,
        "next_step": "",
        "current_sub_task": "",
        "llm_provider": req.llm_provider,
        "llm_model": req.llm_model or "",
        "ollama_url": req.ollama_url or "",
        "hitl_approved": False,
        "hitl_edited_findings": "",
        "error": "",
    }
    graph = request.app.state.graph
    config = _config_for(thread_id)

    async def gen():
        yield _sse("thread", {"thread_id": thread_id})
        async for ev in _stream_events(graph, initial_state, config):
            yield ev

    return EventSourceResponse(gen())


@app.post("/api/research/{thread_id}/resume")
async def resume_research(thread_id: str, action: ResumeAction, request: Request):
    graph = request.app.state.graph
    config = _config_for(thread_id)

    state = await graph.aget_state(config)
    if not state.values:
        raise HTTPException(404, "Unknown thread_id")

    resume_payload = action.model_dump(exclude_none=True)

    async def gen():
        async for ev in _stream_events(graph, Command(resume=resume_payload), config):
            yield ev

    return EventSourceResponse(gen())


@app.get("/api/research/{thread_id}/state")
async def get_state(thread_id: str, request: Request):
    graph = request.app.state.graph
    config = _config_for(thread_id)
    state = await graph.aget_state(config)
    if not state.values:
        raise HTTPException(404, "Unknown thread_id")
    return {"values": state.values, "next": list(state.next)}
