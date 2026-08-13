# tests/test_graph.py
"""Unit tests for app/graph.py. Node functions, routing, and state schema.
All chains are mocked — fully offline."""

import pytest
from unittest.mock import AsyncMock

from langgraph.checkpoint.memory import InMemorySaver

from app import graph
from app.agents import ResearchAgentError
from app.schemas import CritiqueVerdict


def _base_state(**overrides) -> dict:
    state = {
        "main_task": "Explain transformer architecture",
        "research_findings": [],
        "draft": "",
        "critique_notes": "",
        "critique_approved": False,
        "revision_number": 0,
        "next_step": "",
        "current_sub_task": "",
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "ollama_url": "",
        "hitl_approved": False,
        "hitl_edited_findings": "",
        "error": "",
    }
    state.update(overrides)
    return state


class TestBuildGraph:
    def test_graph_compiles_with_checkpointer(self):
        app = graph.build_graph(checkpointer=InMemorySaver())
        assert app is not None

    def test_all_nodes_present(self):
        app = graph.build_graph(checkpointer=InMemorySaver())
        node_names = set(app.get_graph().nodes.keys())
        assert {"supervisor", "researcher", "human_review", "writer", "critiquer"} <= node_names


class TestSupervisorNode:
    @pytest.mark.asyncio
    async def test_routes_to_researcher(self, monkeypatch):
        monkeypatch.setattr(
            graph, "supervisor_chain",
            AsyncMock(return_value={"next_step": "researcher", "task_description": "go"}),
        )
        result = await graph.supervisor_node(_base_state())
        assert result["next_step"] == "researcher"
        assert result["current_sub_task"] == "go"


class TestResearchNode:
    @pytest.mark.asyncio
    async def test_appends_structured_brief(self, monkeypatch):
        brief = {"query": "x", "sub_queries": ["x"], "bullets": ["fact"], "sources": []}
        monkeypatch.setattr(graph, "researcher_agent", AsyncMock(return_value={"output": "fact", "brief": brief}))
        result = await graph.research_node(_base_state(current_sub_task="explain attention"))
        assert result["research_findings"] == [brief]
        assert result["error"] == ""

    @pytest.mark.asyncio
    async def test_agent_failure_surfaces_as_error_not_fake_content(self, monkeypatch):
        async def bad_agent(_input):
            raise ResearchAgentError("search provider down")

        monkeypatch.setattr(graph, "researcher_agent", bad_agent)
        result = await graph.research_node(_base_state(current_sub_task="x"))
        assert "research_findings" not in result
        assert "search provider down" in result["error"]

    @pytest.mark.asyncio
    async def test_falls_back_to_main_task_when_no_sub_task(self, monkeypatch):
        captured = {}

        async def fake_agent(input_dict):
            captured["input"] = input_dict["input"]
            return {"output": "x", "brief": {"query": "x", "sub_queries": [], "bullets": [], "sources": []}}

        monkeypatch.setattr(graph, "researcher_agent", fake_agent)
        state = _base_state(main_task="Explain transformers")
        del state["current_sub_task"]
        await graph.research_node(state)
        assert captured["input"] == "Explain transformers"


class TestWriteNode:
    @pytest.mark.asyncio
    async def test_increments_revision_and_clears_error(self, monkeypatch):
        monkeypatch.setattr(graph, "writer_chain", AsyncMock(return_value="## Key Takeaway\nDone."))
        result = await graph.write_node(_base_state(revision_number=1))
        assert result["revision_number"] == 2
        assert result["error"] == ""

    @pytest.mark.asyncio
    async def test_writer_failure_surfaces_as_error(self, monkeypatch):
        async def bad_chain(_state):
            raise ResearchAgentError("LLM down")

        monkeypatch.setattr(graph, "writer_chain", bad_chain)
        result = await graph.write_node(_base_state())
        assert "draft" not in result
        assert "LLM down" in result["error"]


class TestCritiqueNode:
    @pytest.mark.asyncio
    async def test_approved_routes_to_end(self, monkeypatch):
        monkeypatch.setattr(
            graph, "critique_chain",
            AsyncMock(return_value=CritiqueVerdict(approved=True, summary="great")),
        )
        result = await graph.critique_node(_base_state(draft="x" * 200))
        assert result["next_step"] == "END"
        assert result["critique_approved"] is True
        assert result["critique_notes"].startswith("APPROVED")

    @pytest.mark.asyncio
    async def test_rejected_routes_to_writer_with_fixes(self, monkeypatch):
        monkeypatch.setattr(
            graph, "critique_chain",
            AsyncMock(return_value=CritiqueVerdict(approved=False, summary="needs work", fixes=["Add data", "Fix structure"])),
        )
        result = await graph.critique_node(_base_state(draft="x" * 200))
        assert result["next_step"] == "writer"
        assert result["critique_approved"] is False
        assert "Add data" in result["critique_notes"]


class TestHumanReviewRouting:
    def test_routes_to_researcher_on_research_action(self):
        assert graph._route_after_human_review({"next_step": "researcher"}) == "researcher"

    def test_defaults_to_supervisor(self):
        assert graph._route_after_human_review({"next_step": "supervisor"}) == "supervisor"
        assert graph._route_after_human_review({}) == "supervisor"


class TestSupervisorRouting:
    def test_routes_end(self):
        assert graph._route_after_supervisor({"next_step": "END"}) == graph.END

    def test_routes_writer(self):
        assert graph._route_after_supervisor({"next_step": "writer"}) == "writer"

    def test_unknown_defaults_to_researcher(self):
        assert graph._route_after_supervisor({"next_step": "???"}) == "researcher"


class TestResearchState:
    def test_state_has_required_keys(self):
        required_keys = {
            "main_task", "research_findings", "draft", "critique_notes", "critique_approved",
            "revision_number", "next_step", "current_sub_task",
            "llm_provider", "llm_model", "ollama_url",
            "hitl_approved", "hitl_edited_findings", "error",
        }
        assert required_keys == set(graph.ResearchState.__annotations__.keys())
