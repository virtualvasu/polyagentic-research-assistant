# tests/test_agents.py
"""Unit tests for app/agents.py. All LLM and Tavily calls are mocked — these
tests run fully offline, no API keys required."""

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from app import agents
from app.schemas import CritiqueVerdict, ResearchBullets, Source, SubQueryPlan


def _base_state(**overrides) -> dict:
    state = {
        "main_task": "What is quantum computing?",
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
    }
    state.update(overrides)
    return state


# ─── _is_transient ────────────────────────────────────────────────────────────


class TestIsTransient:
    def test_timeout_is_transient(self):
        assert agents._is_transient(httpx.ConnectTimeout("boom"))

    def test_generic_value_error_is_not_transient(self):
        assert not agents._is_transient(ValueError("bad input"))

    def test_rate_limit_status_is_transient(self):
        resp = MagicMock(status_code=429)
        exc = Exception("rate limited")
        exc.response = resp
        assert agents._is_transient(exc)

    def test_auth_error_status_is_not_transient(self):
        resp = MagicMock(status_code=401)
        exc = Exception("bad key")
        exc.response = resp
        assert not agents._is_transient(exc)


# ─── _get_llm ─────────────────────────────────────────────────────────────────


class TestGetLlm:
    def test_missing_provider_defaults_to_groq(self, monkeypatch):
        monkeypatch.setattr(agents, "get_settings", lambda: MagicMock(groq_api_key="x", default_groq_model="m", llm_timeout_seconds=5))
        from langchain_groq import ChatGroq
        result = agents._get_llm({})
        assert isinstance(result, ChatGroq)

    def test_groq_without_key_raises(self, monkeypatch):
        monkeypatch.setattr(agents, "get_settings", lambda: MagicMock(groq_api_key=None))
        with pytest.raises(agents.LLMProviderError):
            agents._get_llm({"llm_provider": "groq"})

    def test_ollama_provider_instantiation(self, monkeypatch):
        monkeypatch.setattr(agents, "get_settings", lambda: MagicMock(ollama_base_url="http://localhost:11434", llm_timeout_seconds=5))
        from langchain_ollama import ChatOllama
        result = agents._get_llm({"llm_provider": "ollama", "llm_model": "llama3.1:latest"})
        assert isinstance(result, ChatOllama)


# ─── Supervisor Chain (deterministic paths) ───────────────────────────────────


class TestSupervisorChain:
    def setup_method(self):
        self.supervisor = agents.create_supervisor_chain()

    @pytest.mark.asyncio
    async def test_routes_to_researcher_when_no_findings(self):
        result = await self.supervisor(_base_state())
        assert result["next_step"] == "researcher"

    @pytest.mark.asyncio
    async def test_routes_to_writer_after_research(self):
        state = _base_state(research_findings=[{"bullets": ["x"], "sources": [], "sub_queries": [], "query": "q"}])
        result = await self.supervisor(state)
        assert result["next_step"] == "writer"

    @pytest.mark.asyncio
    async def test_routes_to_end_when_approved(self):
        state = _base_state(
            research_findings=[{"bullets": ["x"], "sources": [], "sub_queries": [], "query": "q"}],
            draft="Full draft",
            critique_notes="APPROVED - good",
            critique_approved=True,
        )
        result = await self.supervisor(state)
        assert result["next_step"] == "END"

    @pytest.mark.asyncio
    async def test_routes_to_writer_on_revision_needed(self):
        state = _base_state(
            research_findings=[{"bullets": ["x"], "sources": [], "sub_queries": [], "query": "q"}],
            draft="Full draft",
            critique_notes="1. Fix X",
            critique_approved=False,
            revision_number=1,
        )
        result = await self.supervisor(state)
        assert result["next_step"] == "writer"

    @pytest.mark.asyncio
    async def test_ends_at_max_revisions(self):
        state = _base_state(
            research_findings=[{"bullets": ["x"], "sources": [], "sub_queries": [], "query": "q"}],
            draft="Full draft",
            critique_notes="1. Fix X",
            critique_approved=False,
            revision_number=3,
        )
        result = await self.supervisor(state)
        assert result["next_step"] == "END"


# ─── Researcher ────────────────────────────────────────────────────────────────


class TestResearcher:
    @pytest.mark.asyncio
    async def test_happy_path_returns_structured_brief(self, monkeypatch):
        monkeypatch.setattr(agents, "_get_llm", lambda state: MagicMock())
        monkeypatch.setattr(
            agents, "_plan_sub_queries", AsyncMock(return_value=["angle one", "angle two"])
        )

        async def fake_search(query):
            return [{"title": f"Result for {query}", "url": f"http://example.com/{query}", "content": "some content"}]

        monkeypatch.setattr(agents, "_search_one", fake_search)
        monkeypatch.setattr(
            agents,
            "_invoke_structured",
            AsyncMock(return_value=ResearchBullets(bullets=["Fact one [Source: x]", "Fact two [Source: y]"])),
        )

        researcher = agents.create_researcher_agent()
        result = await researcher({"input": "quantum computing"})

        assert "brief" in result
        assert result["brief"]["sub_queries"] == ["angle one", "angle two"]
        assert len(result["brief"]["bullets"]) == 2
        assert len(result["brief"]["sources"]) == 2  # deduped by URL, one per query

    @pytest.mark.asyncio
    async def test_dedupes_results_by_url(self, monkeypatch):
        monkeypatch.setattr(agents, "_get_llm", lambda state: MagicMock())
        monkeypatch.setattr(agents, "_plan_sub_queries", AsyncMock(return_value=["a", "b"]))

        async def fake_search(query):
            return [{"title": "Same page", "url": "http://example.com/dupe", "content": "..."}]

        monkeypatch.setattr(agents, "_search_one", fake_search)
        monkeypatch.setattr(
            agents, "_invoke_structured", AsyncMock(return_value=ResearchBullets(bullets=["fact"]))
        )

        researcher = agents.create_researcher_agent()
        result = await researcher({"input": "topic"})
        assert len(result["brief"]["sources"]) == 1

    @pytest.mark.asyncio
    async def test_all_searches_failing_raises_search_error(self, monkeypatch):
        monkeypatch.setattr(agents, "_get_llm", lambda state: MagicMock())
        monkeypatch.setattr(agents, "_plan_sub_queries", AsyncMock(return_value=["a"]))

        async def failing_search(query):
            raise agents.SearchProviderError("tavily down")

        monkeypatch.setattr(agents, "_search_one", failing_search)

        researcher = agents.create_researcher_agent()
        with pytest.raises(agents.SearchProviderError):
            await researcher({"input": "topic"})

    @pytest.mark.asyncio
    async def test_summarization_failure_falls_back_to_raw_snippets(self, monkeypatch):
        """A failed structured-output call must not crash the whole research
        cycle or fabricate placeholder text — it should degrade to using the
        raw search snippets as bullets."""
        monkeypatch.setattr(agents, "_get_llm", lambda state: MagicMock())
        monkeypatch.setattr(agents, "_plan_sub_queries", AsyncMock(return_value=["a"]))

        async def fake_search(query):
            return [{"title": "T", "url": "http://x.com", "content": "real content here"}]

        monkeypatch.setattr(agents, "_search_one", fake_search)
        monkeypatch.setattr(
            agents, "_invoke_structured", AsyncMock(side_effect=agents.LLMProviderError("boom"))
        )

        researcher = agents.create_researcher_agent()
        result = await researcher({"input": "topic"})
        assert "real content here" in result["brief"]["bullets"][0]


# ─── Writer ────────────────────────────────────────────────────────────────────


class TestWriter:
    @pytest.mark.asyncio
    async def test_returns_draft_content(self, monkeypatch):
        response = MagicMock(content="## Key Takeaway\nSomething useful.")
        monkeypatch.setattr(agents, "_get_llm", lambda state: MagicMock())
        monkeypatch.setattr(agents, "_invoke", AsyncMock(return_value=response))

        writer = agents.create_writer_chain()
        draft = await writer(_base_state(research_findings=[{"bullets": ["fact"], "sources": [], "sub_queries": [], "query": "q"}]))
        assert "Something useful" in draft

    @pytest.mark.asyncio
    async def test_empty_response_raises(self, monkeypatch):
        response = MagicMock(content="")
        monkeypatch.setattr(agents, "_get_llm", lambda state: MagicMock())
        monkeypatch.setattr(agents, "_invoke", AsyncMock(return_value=response))

        writer = agents.create_writer_chain()
        with pytest.raises(agents.LLMProviderError):
            await writer(_base_state())

    def test_formats_hitl_edited_findings_when_present(self):
        state = _base_state(hitl_approved=True, hitl_edited_findings="Edited text wins")
        assert agents._format_research_for_prompt(state) == "Edited text wins"

    def test_formats_structured_findings_when_no_hitl_edit(self):
        state = _base_state(
            research_findings=[{"bullets": ["fact one"], "sources": [{"title": "T", "url": "http://x.com"}], "sub_queries": [], "query": "q"}]
        )
        formatted = agents._format_research_for_prompt(state)
        assert "fact one" in formatted
        assert "http://x.com" in formatted


# ─── Critique ──────────────────────────────────────────────────────────────────


class TestCritique:
    @pytest.mark.asyncio
    async def test_short_draft_auto_rejected(self):
        critique = agents.create_critique_chain()
        verdict = await critique(_base_state(draft="too short"))
        assert verdict.approved is False

    @pytest.mark.asyncio
    async def test_max_revisions_auto_approved(self):
        critique = agents.create_critique_chain()
        verdict = await critique(_base_state(draft="x" * 200, revision_number=3))
        assert verdict.approved is True

    @pytest.mark.asyncio
    async def test_delegates_to_structured_llm_call(self, monkeypatch):
        monkeypatch.setattr(agents, "_get_llm", lambda state: MagicMock())
        expected = CritiqueVerdict(approved=False, summary="needs work", fixes=["Add citations"])
        monkeypatch.setattr(agents, "_invoke_structured", AsyncMock(return_value=expected))

        critique = agents.create_critique_chain()
        verdict = await critique(_base_state(draft="x" * 200, revision_number=0))
        assert verdict == expected
