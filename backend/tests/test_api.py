# tests/test_api.py
"""Integration tests for the FastAPI service. Agent chains are monkeypatched
at the app.graph module level (node functions look them up as globals on
every call, so patching after graph construction still takes effect) —
no real LLM/Tavily calls happen here."""

import json

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CHECKPOINT_DB_PATH", str(tmp_path / "test_checkpoints.db"))
    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def _parse_sse(text: str) -> list[dict]:
    text = text.replace("\r\n", "\n")
    events = []
    for block in text.strip().split("\n\n"):
        data_lines = [l[len("data:"):].strip() for l in block.splitlines() if l.startswith("data:")]
        if data_lines:
            events.append(json.loads("".join(data_lines)))
    return events


class TestHealth:
    def test_reports_configured_providers(self, client, monkeypatch):
        from app import main as main_module

        monkeypatch.setattr(
            main_module, "get_settings",
            lambda: type("S", (), {"groq_api_key": "x", "tavily_api_key": "y", "ollama_base_url": "http://localhost:11434"})(),
        )
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["groq_configured"] is True
        assert body["tavily_configured"] is True

    def test_reports_unconfigured_providers(self, client, monkeypatch):
        from app import main as main_module

        monkeypatch.setattr(
            main_module, "get_settings",
            lambda: type("S", (), {"groq_api_key": None, "tavily_api_key": None, "ollama_base_url": "http://localhost:11434"})(),
        )
        r = client.get("/health")
        body = r.json()
        assert body["groq_configured"] is False
        assert body["tavily_configured"] is False


class TestResearchFlow:
    def test_stream_runs_until_hitl_interrupt(self, client, monkeypatch):
        from app import graph as graph_module

        async def fake_supervisor(state):
            return {"next_step": "researcher", "task_description": "go"}

        async def fake_researcher(input_dict):
            return {
                "output": "fact",
                "brief": {"query": "q", "sub_queries": ["q"], "bullets": ["fact one"], "sources": []},
            }

        monkeypatch.setattr(graph_module, "supervisor_chain", fake_supervisor)
        monkeypatch.setattr(graph_module, "researcher_agent", fake_researcher)

        with client.stream(
            "POST", "/api/research/stream", json={"topic": "test topic", "llm_provider": "groq"}
        ) as r:
            assert r.status_code == 200
            events = _parse_sse(r.read().decode())

        thread_events = [e for e in events if "thread_id" in e]
        assert len(thread_events) == 1
        step_events = [e for e in events if "node" in e and "output" in e]
        assert any(e["node"] == "researcher" for e in step_events)
        interrupt_events = [e for e in events if "payload" in e]
        assert len(interrupt_events) == 1
        assert interrupt_events[0]["payload"]["type"] == "research_review"

    def test_resume_after_hitl_reaches_done(self, client, monkeypatch):
        from app import graph as graph_module

        async def fake_supervisor(state):
            if state.get("critique_approved"):
                return {"next_step": "END", "task_description": "done"}
            if not state.get("research_findings"):
                return {"next_step": "researcher", "task_description": "go"}
            if not state.get("draft"):
                return {"next_step": "writer", "task_description": "write"}
            return {"next_step": "writer", "task_description": "revise"}

        async def fake_researcher(input_dict):
            return {
                "output": "fact",
                "brief": {"query": "q", "sub_queries": ["q"], "bullets": ["fact one"], "sources": []},
            }

        async def fake_writer(state):
            return "## Key Takeaway\nDone deal."

        from app.schemas import CritiqueVerdict

        async def fake_critique(state):
            return CritiqueVerdict(approved=True, summary="good")

        monkeypatch.setattr(graph_module, "supervisor_chain", fake_supervisor)
        monkeypatch.setattr(graph_module, "researcher_agent", fake_researcher)
        monkeypatch.setattr(graph_module, "writer_chain", fake_writer)
        monkeypatch.setattr(graph_module, "critique_chain", fake_critique)

        with client.stream(
            "POST", "/api/research/stream", json={"topic": "test topic", "llm_provider": "groq"}
        ) as r:
            events = _parse_sse(r.read().decode())
        thread_id = next(e["thread_id"] for e in events if "thread_id" in e)

        with client.stream(
            "POST", f"/api/research/{thread_id}/resume", json={"action": "approve", "edited_text": "fact one"}
        ) as r:
            assert r.status_code == 200
            events = _parse_sse(r.read().decode())

        done_events = [e for e in events if "final_state" in e]
        assert len(done_events) == 1
        assert "Done deal" in done_events[0]["final_state"]["draft"]

    def test_resume_unknown_thread_returns_404(self, client):
        r = client.post("/api/research/unknown-id/resume", json={"action": "approve"})
        assert r.status_code == 404

    def test_state_unknown_thread_returns_404(self, client):
        r = client.get("/api/research/unknown-id/state")
        assert r.status_code == 404
