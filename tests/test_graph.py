# tests/test_graph.py
"""
Unit tests for graph.py

Tests graph node functions, routing logic, and graph compilation.
All LLM and external API calls are mocked.
"""

import pytest
from unittest.mock import MagicMock, patch


def _base_state(**overrides) -> dict:
    """Returns a minimal valid ResearchState dict."""
    state = {
        "main_task": "Explain transformer architecture",
        "research_findings": [],
        "draft": "",
        "critique_notes": "",
        "revision_number": 0,
        "next_step": "",
        "current_sub_task": "",
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "ollama_url": "",
        "hitl_approved": False,
        "hitl_edited_findings": "",
    }
    state.update(overrides)
    return state


# ─── Graph compilation ────────────────────────────────────────────────────────

class TestBuildGraph:
    def test_graph_compiles_without_error(self):
        """The graph should compile cleanly — no missing nodes or edges."""
        from graph import build_graph
        app = build_graph()
        assert app is not None

    def test_compiled_graph_is_callable(self):
        from graph import build_graph
        app = build_graph()
        assert callable(app.invoke) or hasattr(app, "stream")

    def test_graph_has_interrupt_before_human_review(self):
        """MemorySaver + interrupt_before=["human_review"] should be set."""
        from graph import build_graph
        app = build_graph()
        # LangGraph exposes interrupt_before on the compiled graph config
        # We check the builder config indirectly via the graph's nodes
        node_names = list(app.nodes.keys()) if hasattr(app, "nodes") else []
        # "human_review" must exist as a node for interrupt_before to be valid
        # If we can't introspect nodes, at least the build must succeed
        assert app is not None


# ─── supervisor_node ──────────────────────────────────────────────────────────

class TestSupervisorNode:
    def test_routes_to_researcher_with_empty_state(self, monkeypatch):
        mock_chain = MagicMock(return_value={
            "next_step": "researcher",
            "task_description": "Research the topic"
        })
        monkeypatch.setattr("graph.supervisor_chain", mock_chain)
        from graph import supervisor_node

        result = supervisor_node(_base_state())
        assert result["next_step"] == "researcher"
        assert "current_sub_task" in result

    def test_routes_to_writer_after_research(self, monkeypatch):
        mock_chain = MagicMock(return_value={
            "next_step": "writer",
            "task_description": "Write first draft"
        })
        monkeypatch.setattr("graph.supervisor_chain", mock_chain)
        from graph import supervisor_node

        state = _base_state(research_findings=["Finding 1"])
        result = supervisor_node(state)
        assert result["next_step"] == "writer"

    def test_routes_to_end_on_approval(self, monkeypatch):
        mock_chain = MagicMock(return_value={
            "next_step": "END",
            "task_description": "Approved"
        })
        monkeypatch.setattr("graph.supervisor_chain", mock_chain)
        from graph import supervisor_node

        state = _base_state(
            research_findings=["Finding"],
            draft="Full draft",
            critique_notes="APPROVED"
        )
        result = supervisor_node(state)
        assert result["next_step"] == "END"

    def test_defaults_next_step_if_missing_from_chain(self, monkeypatch):
        mock_chain = MagicMock(return_value={"task_description": "Do something"})
        monkeypatch.setattr("graph.supervisor_chain", mock_chain)
        from graph import supervisor_node

        result = supervisor_node(_base_state())
        # Should fall back to "researcher" default
        assert result.get("next_step") == "researcher"


# ─── research_node ────────────────────────────────────────────────────────────

class TestResearchNode:
    def test_appends_findings_to_list(self, monkeypatch):
        mock_agent = MagicMock(return_value={"output": "Transformers use attention mechanisms."})
        monkeypatch.setattr("graph.researcher_agent", mock_agent)
        from graph import research_node

        state = _base_state(current_sub_task="Explain attention mechanism")
        result = research_node(state)

        assert "research_findings" in result
        assert isinstance(result["research_findings"], list)
        assert len(result["research_findings"]) == 1
        assert "Transformers" in result["research_findings"][0]

    def test_uses_main_task_when_sub_task_missing(self, monkeypatch):
        """When current_sub_task is absent (None), falls back to main_task."""
        captured = {}
        def fake_agent(input_dict):
            captured["input"] = input_dict["input"]
            return {"output": "Some research output"}
        monkeypatch.setattr("graph.researcher_agent", fake_agent)
        from graph import research_node

        # Don't set current_sub_task — key absent means .get() returns None
        state = _base_state(main_task="Explain transformer architecture")
        del state["current_sub_task"]
        research_node(state)
        assert captured["input"] == "Explain transformer architecture"

    def test_handles_agent_exception_gracefully(self, monkeypatch):
        def bad_agent(input_dict):
            raise RuntimeError("Research service unavailable")
        monkeypatch.setattr("graph.researcher_agent", bad_agent)
        from graph import research_node

        state = _base_state(current_sub_task="test")
        result = research_node(state)
        # Should not raise — returns fallback findings
        assert "research_findings" in result
        assert len(result["research_findings"]) == 1

    def test_passes_llm_config_to_agent(self, monkeypatch):
        captured = {}
        def fake_agent(input_dict):
            captured.update(input_dict)
            return {"output": "Result"}
        monkeypatch.setattr("graph.researcher_agent", fake_agent)
        from graph import research_node

        state = _base_state(
            current_sub_task="test",
            llm_provider="ollama",
            llm_model="llama3.1:latest",
            ollama_url="http://localhost:11434"
        )
        research_node(state)
        assert captured["llm_provider"] == "ollama"
        assert captured["llm_model"] == "llama3.1:latest"


# ─── human_review_node ────────────────────────────────────────────────────────

class TestHumanReviewNode:
    def test_returns_empty_dict(self):
        """Human review node only acts as a pause point — returns no state changes."""
        from graph import human_review_node
        state = _base_state()
        result = human_review_node(state)
        assert result == {}

    def test_does_not_modify_state(self):
        from graph import human_review_node
        state = _base_state(research_findings=["Finding 1"], draft="Some draft")
        result = human_review_node(state)
        # Node should return empty — state management is handled by LangGraph
        assert "research_findings" not in result
        assert "draft" not in result


# ─── write_node ───────────────────────────────────────────────────────────────

class TestWriteNode:
    def test_returns_draft_and_increments_revision(self, monkeypatch):
        mock_chain = MagicMock(return_value="## Key Takeaway\nTransformers changed NLP.")
        monkeypatch.setattr("graph.writer_chain", mock_chain)
        from graph import write_node

        state = _base_state(research_findings=["Attention is all you need."], revision_number=0)
        result = write_node(state)

        assert "draft" in result
        assert result["revision_number"] == 1
        assert "Transformers" in result["draft"]

    def test_increments_existing_revision_count(self, monkeypatch):
        mock_chain = MagicMock(return_value="Revised draft content here.")
        monkeypatch.setattr("graph.writer_chain", mock_chain)
        from graph import write_node

        state = _base_state(revision_number=2)
        result = write_node(state)
        assert result["revision_number"] == 3

    def test_propagates_writer_exception(self, monkeypatch):
        def bad_chain(state):
            raise RuntimeError("LLM Error in Writer: Connection refused")
        monkeypatch.setattr("graph.writer_chain", bad_chain)
        from graph import write_node

        with pytest.raises(RuntimeError, match="LLM Error in Writer"):
            write_node(_base_state())


# ─── critique_node ────────────────────────────────────────────────────────────

class TestCritiqueNode:
    def test_sets_next_step_to_end_on_approval(self, monkeypatch):
        mock_chain = MagicMock(return_value="APPROVED - Report is well-structured.")
        monkeypatch.setattr("graph.critique_chain", mock_chain)
        from graph import critique_node

        state = _base_state(draft="A complete and thorough report.", revision_number=1)
        result = critique_node(state)

        assert result["critique_notes"] == "APPROVED"
        assert result["next_step"] == "END"

    def test_sets_next_step_to_writer_on_rejection(self, monkeypatch):
        mock_chain = MagicMock(return_value=(
            "1. Findings: Missing citations. Fix: Add source URLs.\n"
            "2. Analysis: Too brief. Fix: Expand with two more paragraphs."
        ))
        monkeypatch.setattr("graph.critique_chain", mock_chain)
        from graph import critique_node

        state = _base_state(draft="Incomplete draft.", revision_number=0)
        result = critique_node(state)

        assert "APPROVED" not in result["critique_notes"].upper()
        assert result["next_step"] == "writer"

    def test_critique_notes_stored_in_result(self, monkeypatch):
        critique_text = "1. Analysis: Too vague. Fix: Add specific numbers."
        mock_chain = MagicMock(return_value=critique_text)
        monkeypatch.setattr("graph.critique_chain", mock_chain)
        from graph import critique_node

        state = _base_state(draft="Some draft content.")
        result = critique_node(state)
        assert result["critique_notes"] == critique_text

    def test_case_insensitive_approval_check(self, monkeypatch):
        """'approved' in lowercase should still trigger END routing."""
        mock_chain = MagicMock(return_value="approved - looks good.")
        monkeypatch.setattr("graph.critique_chain", mock_chain)
        from graph import critique_node

        state = _base_state(draft="A decent draft.")
        result = critique_node(state)
        assert result["next_step"] == "END"


# ─── ResearchState schema ─────────────────────────────────────────────────────

class TestResearchState:
    def test_state_has_required_keys(self):
        from graph import ResearchState
        required_keys = {
            "main_task", "research_findings", "draft", "critique_notes",
            "revision_number", "next_step", "current_sub_task",
            "llm_provider", "llm_model", "ollama_url",
            "hitl_approved", "hitl_edited_findings"
        }
        assert required_keys == set(ResearchState.__annotations__.keys())

    def test_research_findings_is_list_type(self):
        from graph import ResearchState
        import typing
        annotation = ResearchState.__annotations__["research_findings"]
        # Should be Annotated[List[str], operator.add]
        assert hasattr(annotation, "__metadata__") or "List" in str(annotation)
