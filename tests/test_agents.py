# tests/test_agents.py
"""
Unit tests for agents.py

All LLM and Tavily calls are mocked — these tests run offline
without requiring any API keys.
"""

import pytest
from unittest.mock import MagicMock, patch
import agents


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _mock_llm_response(content: str) -> MagicMock:
    """Returns a mock LLM response object with a .content attribute."""
    resp = MagicMock()
    resp.content = content
    return resp


def _base_state(**overrides) -> dict:
    """Returns a minimal valid ResearchState dict for testing."""
    state = {
        "main_task": "What is quantum computing?",
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


# ─── _call_llm ────────────────────────────────────────────────────────────────

class TestCallLlm:
    def test_prefers_invoke_over_run(self):
        obj = MagicMock()
        obj.invoke.return_value = "from_invoke"
        result = agents._call_llm(obj, "input")
        assert result == "from_invoke"
        obj.invoke.assert_called_once_with("input")

    def test_falls_back_to_run(self):
        class NoInvoke:
            def run(self, arg):
                return f"ran_{arg}"
        assert agents._call_llm(NoInvoke(), "x") == "ran_x"

    def test_falls_back_to_callable(self):
        fn = lambda x: f"called_{x}"
        assert agents._call_llm(fn, "x") == "called_x"

    def test_raises_when_nothing_works(self):
        with pytest.raises(AttributeError):
            agents._call_llm(object(), "x")


# ─── _get_llm ─────────────────────────────────────────────────────────────────

class TestGetLlm:
    def test_returns_default_for_none_input(self):
        result = agents._get_llm(None)
        assert result is agents.llm

    def test_returns_default_for_non_dict(self):
        result = agents._get_llm("not a dict")
        assert result is agents.llm

    def test_returns_default_when_provider_missing(self):
        result = agents._get_llm({"llm_model": "something"})
        assert result is agents.llm

    def test_groq_provider_instantiation(self):
        from langchain_groq import ChatGroq
        result = agents._get_llm({"llm_provider": "groq", "llm_model": "gemma2-9b-it"})
        assert isinstance(result, ChatGroq)

    def test_ollama_provider_instantiation(self):
        from langchain_ollama import ChatOllama
        result = agents._get_llm({
            "llm_provider": "ollama",
            "llm_model": "llama3.1:latest",
            "ollama_url": "http://localhost:11434"
        })
        assert isinstance(result, ChatOllama)

    def test_groq_fallback_on_exception(self, monkeypatch):
        """If ChatGroq() raises during _get_llm, it falls back to agents.llm."""
        import langchain_groq

        def always_fails(*a, **kw):
            raise RuntimeError("Simulated Groq init failure")

        monkeypatch.setattr(langchain_groq, "ChatGroq", always_fails)
        result = agents._get_llm({"llm_provider": "groq", "llm_model": "x"})
        assert result is agents.llm



# ─── Supervisor Chain ─────────────────────────────────────────────────────────

class TestSupervisorChain:
    def setup_method(self):
        self.supervisor = agents.create_supervisor_chain()

    def test_routes_to_researcher_when_no_findings(self):
        state = _base_state()
        result = self.supervisor(state)
        assert result["next_step"] == "researcher"

    def test_routes_to_writer_when_findings_exist_no_draft(self):
        state = _base_state(research_findings=["Finding 1"])
        result = self.supervisor(state)
        assert result["next_step"] == "writer"

    def test_routes_to_end_when_approved(self):
        state = _base_state(
            research_findings=["Finding 1"],
            draft="A complete draft with real content.",
            critique_notes="APPROVED - Report is ready."
        )
        result = self.supervisor(state)
        assert result["next_step"] == "END"

    def test_routes_to_writer_when_critique_requests_revision(self):
        state = _base_state(
            research_findings=["Finding 1"],
            draft="A draft needing revision.",
            critique_notes="1. Findings: Problem: Missing data. Fix: Add statistics.",
            revision_number=1
        )
        result = self.supervisor(state)
        assert result["next_step"] == "writer"

    def test_ends_when_max_revisions_reached(self):
        state = _base_state(
            research_findings=["Finding 1"],
            draft="A draft.",
            critique_notes="Still needs work.",
            revision_number=3
        )
        result = self.supervisor(state)
        assert result["next_step"] == "END"

    def test_returns_dict_with_required_keys(self):
        state = _base_state()
        result = self.supervisor(state)
        assert "next_step" in result
        assert "task_description" in result


# ─── Researcher Agent ─────────────────────────────────────────────────────────

class TestResearcherAgent:
    def setup_method(self):
        self.researcher = agents.create_researcher_agent()

    def test_returns_dict_with_output_key(self, monkeypatch):
        fake_tavily = MagicMock()
        fake_tavily.invoke.return_value = {
            "results": [
                {"title": "Quantum Computing Overview",
                 "url": "https://example.com",
                 "content": "Quantum computers use qubits."}
            ]
        }
        monkeypatch.setattr(agents, "tavily_tool", fake_tavily)

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _mock_llm_response(
            "- Quantum computers use qubits [Source: https://example.com]"
        )
        monkeypatch.setattr(agents, "_get_llm", lambda x: mock_llm)

        result = self.researcher({"input": "quantum computing"})
        assert "output" in result
        assert isinstance(result["output"], str)
        assert len(result["output"]) > 0

    def test_handles_empty_search_results_gracefully(self, monkeypatch):
        fake_tavily = MagicMock()
        fake_tavily.invoke.return_value = {"results": []}
        monkeypatch.setattr(agents, "tavily_tool", fake_tavily)

        result = self.researcher({"input": "very obscure topic xyz123"})
        assert "output" in result

    def test_handles_tavily_exception_gracefully(self, monkeypatch):
        def bad_tavily(*a, **kw):
            raise ConnectionError("Tavily unavailable")
        monkeypatch.setattr(agents, "tavily_tool", bad_tavily)

        result = self.researcher({"input": "test query"})
        # Should not raise — returns a fallback dict
        assert "output" in result

    def test_ignores_trivial_queries(self, monkeypatch):
        fake_tavily = MagicMock()
        fake_tavily.invoke.return_value = {"results": []}
        monkeypatch.setattr(agents, "tavily_tool", fake_tavily)

        result = self.researcher({"input": "Continue work"})
        assert "output" in result


# ─── Writer Chain ─────────────────────────────────────────────────────────────

class TestWriterChain:
    def setup_method(self):
        self.writer = agents.create_writer_chain()

    def test_produces_non_empty_string(self, monkeypatch):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _mock_llm_response(
            "## Key Takeaway\nQuantum computing will break RSA.\n\n"
            "## Findings\nShor's algorithm factors large integers efficiently.\n\n"
            "## Analysis\nThis threatens current public-key infrastructure.\n\n"
            "## Bottom Line\nTransition to post-quantum cryptography now."
        )
        monkeypatch.setattr(agents, "_get_llm", lambda x: mock_llm)

        state = _base_state(research_findings=["Shor's algorithm is a quantum algorithm."])
        result = self.writer(state)
        assert isinstance(result, str)
        assert len(result) > 50

    def test_uses_hitl_edited_findings_when_approved(self, monkeypatch):
        """When HITL is approved with edited text, writer should use edited findings."""
        captured_prompts = []

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = lambda prompt: (
            captured_prompts.append(prompt) or _mock_llm_response("A good draft.")
        )
        monkeypatch.setattr(agents, "_get_llm", lambda x: mock_llm)

        state = _base_state(
            research_findings=["Original findings"],
            hitl_approved=True,
            hitl_edited_findings="User-edited findings with extra context"
        )
        self.writer(state)
        # The prompt sent to the LLM should contain the edited text
        assert "User-edited findings with extra context" in captured_prompts[0]

    def test_raises_runtime_error_on_llm_failure(self, monkeypatch):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("LLM unavailable")
        monkeypatch.setattr(agents, "_get_llm", lambda x: mock_llm)

        state = _base_state(research_findings=["Some findings"])
        with pytest.raises(RuntimeError, match="LLM Error in Writer"):
            self.writer(state)


# ─── Critique Chain ───────────────────────────────────────────────────────────

class TestCritiqueChain:
    def setup_method(self):
        self.critiquer = agents.create_critique_chain()

    def test_rejects_short_draft(self):
        state = _base_state(draft="Too short.")
        result = self.critiquer(state)
        assert "REJECTED" in result.upper()

    def test_auto_approves_at_max_revisions(self):
        long_draft = "This is a valid draft. " * 20  # > 100 chars
        state = _base_state(draft=long_draft, revision_number=3)
        result = self.critiquer(state)
        assert "APPROVED" in result.upper()

    def test_returns_approved_string_from_llm(self, monkeypatch):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _mock_llm_response(
            "APPROVED - The draft directly addresses the topic with cited evidence."
        )
        monkeypatch.setattr(agents, "_get_llm", lambda x: mock_llm)

        long_draft = "A well-written report with sufficient content. " * 5
        state = _base_state(draft=long_draft, revision_number=1)
        result = self.critiquer(state)
        assert "APPROVED" in result.upper()

    def test_returns_revision_notes_from_llm(self, monkeypatch):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _mock_llm_response(
            "1. Findings: Problem: Missing sources. Fix: Add citations.\n"
            "2. Analysis: Problem: Too vague. Fix: Add specific numbers."
        )
        monkeypatch.setattr(agents, "_get_llm", lambda x: mock_llm)

        long_draft = "A draft with some content that needs revision. " * 5
        state = _base_state(draft=long_draft, revision_number=0)
        result = self.critiquer(state)
        assert "APPROVED" not in result.upper()
        assert len(result) > 10

    def test_raises_runtime_error_on_llm_failure(self, monkeypatch):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM down")
        monkeypatch.setattr(agents, "_get_llm", lambda x: mock_llm)

        long_draft = "A valid draft with enough content for the test. " * 5
        state = _base_state(draft=long_draft, revision_number=0)
        with pytest.raises(RuntimeError, match="LLM Error in Critiquer"):
            self.critiquer(state)
