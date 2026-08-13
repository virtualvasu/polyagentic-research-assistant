# app/agents.py

import asyncio
import logging
from functools import lru_cache
from typing import Any

import httpx
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.prompts import (
    critique_prompt_template,
    research_summary_prompt_template,
    sub_query_prompt_template,
    supervisor_prompt_template,
    writer_prompt_template,
)
from app.schemas import CritiqueVerdict, ResearchBullets, Source, SubQueryPlan, SupervisorDecision

logger = logging.getLogger(__name__)


# ─── Errors ──────────────────────────────────────────────────────────────────


class ResearchAgentError(Exception):
    """Base class for expected, user-facing agent failures. These propagate
    to the API layer instead of being masked as fake success content."""


class LLMProviderError(ResearchAgentError):
    """The configured LLM provider failed to initialize or respond."""


class SearchProviderError(ResearchAgentError):
    """The web search provider failed."""


# ─── Retry policy ────────────────────────────────────────────────────────────
# Retries transient failures (timeouts, connection errors, 429/5xx). Does NOT
# retry on auth errors (invalid/expired API key) — those are never transient
# and should surface immediately with a clear message.


def _is_transient(exc: BaseException) -> bool:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status in (408, 429, 500, 502, 503, 504):
        return True
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadTimeout))


def _retrying():
    settings = get_settings()
    return retry(
        reraise=True,
        stop=stop_after_attempt(settings.llm_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception(_is_transient),
    )


# ─── LLM / tool factories ────────────────────────────────────────────────────
# Constructed lazily (never at import time) so a missing/invalid key for one
# provider can't crash the whole process when only the other provider is
# in use.


def _get_llm(state_or_dict: dict | None):
    """Builds an LLM client from per-run config. Raises LLMProviderError on
    failure instead of silently substituting a different provider than the
    one the user selected."""
    settings = get_settings()
    cfg = state_or_dict if isinstance(state_or_dict, dict) else {}
    provider = (cfg.get("llm_provider") or "groq").lower()
    model_name = cfg.get("llm_model")

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=model_name or "llama3.1:latest",
                temperature=0.3,
                base_url=cfg.get("ollama_url") or settings.ollama_base_url,
                timeout=settings.llm_timeout_seconds,
            )
        except Exception as e:
            raise LLMProviderError(f"Could not initialize Ollama ({model_name}): {e}") from e

    if not settings.groq_api_key:
        raise LLMProviderError("GROQ_API_KEY is not configured.")
    try:
        return ChatGroq(
            model=model_name or settings.default_groq_model,
            temperature=0.3,
            max_tokens=4096,
            groq_api_key=settings.groq_api_key,
            timeout=settings.llm_timeout_seconds,
        )
    except Exception as e:
        raise LLMProviderError(f"Could not initialize Groq ({model_name}): {e}") from e


@lru_cache
def _tavily_tool() -> TavilySearch:
    settings = get_settings()
    if not settings.tavily_api_key:
        raise SearchProviderError("TAVILY_API_KEY is not configured.")
    return TavilySearch(
        max_results=5,
        topic="general",
        include_answer=False,
        include_raw_content=False,
        search_depth="basic",
        tavily_api_key=settings.tavily_api_key,
    )


async def _invoke(llm_obj, prompt: str):
    @_retrying()
    async def _do():
        return await llm_obj.ainvoke(prompt)

    try:
        return await _do()
    except ResearchAgentError:
        raise
    except Exception as e:
        raise LLMProviderError(str(e)) from e


async def _invoke_structured(llm_obj, schema, prompt: str):
    structured = llm_obj.with_structured_output(schema)

    @_retrying()
    async def _do():
        return await structured.ainvoke(prompt)

    try:
        return await _do()
    except ResearchAgentError:
        raise
    except Exception as e:
        raise LLMProviderError(str(e)) from e


# ─── SUPERVISOR ──────────────────────────────────────────────────────────────


def create_supervisor_chain():
    """Deterministic routing rules first; LLM (structured output) fallback
    only when state doesn't match a known pattern. Keeps routing immune to
    LLM JSON-parsing failures for the common paths."""

    async def supervisor_invoke(state: dict) -> dict:
        research = state.get("research_findings", [])
        revision = state.get("revision_number", 0)
        has_research = len(research) > 0
        has_draft = bool(state.get("draft", "").strip())
        approved = bool(state.get("critique_approved", False))
        has_critique = bool(state.get("critique_notes"))
        settings = get_settings()

        if approved and has_draft:
            return {"next_step": "END", "task_description": "Report approved and complete"}

        if not has_research:
            # task_description doubles as the literal research topic (see
            # research_node) — keep it a clean query, not a log sentence.
            return {
                "next_step": "researcher",
                "task_description": state.get("main_task", ""),
            }

        if has_research and not has_draft:
            return {"next_step": "writer", "task_description": "Write the first draft based on research findings"}

        if has_draft and not has_critique:
            return {"next_step": "writer", "task_description": "Prepare draft for critique"}

        if has_critique and not approved and revision < settings.max_revisions:
            return {"next_step": "writer", "task_description": "Revise the draft based on critique feedback"}

        if revision >= settings.max_revisions:
            return {"next_step": "END", "task_description": "Maximum revisions reached, finalizing report"}

        # Fallback: ambiguous state, ask the LLM for a structured decision.
        research_text = "\n---\n".join(research) if research else "No research yet."
        prompt = supervisor_prompt_template.format(
            main_task=state.get("main_task", ""),
            research_findings=research_text,
            draft=state.get("draft", "No draft yet."),
            critique_notes=state.get("critique_notes", "No critique yet."),
            revision_number=revision,
        )
        try:
            llm_inst = _get_llm(state)
            decision: SupervisorDecision = await _invoke_structured(llm_inst, SupervisorDecision, prompt)
            return {"next_step": decision.next_step, "task_description": decision.task_description}
        except ResearchAgentError as e:
            logger.warning("Supervisor LLM fallback failed (%s); defaulting to writer", e)
            return {"next_step": "writer", "task_description": "Continue with draft creation"}

    return supervisor_invoke


# ─── RESEARCHER ──────────────────────────────────────────────────────────────


async def _plan_sub_queries(llm, topic: str) -> list[str]:
    settings = get_settings()
    prompt = sub_query_prompt_template.format(topic=topic)
    try:
        plan: SubQueryPlan = await _invoke_structured(llm, SubQueryPlan, prompt)
        queries = [q.strip() for q in plan.queries if q.strip()]
    except ResearchAgentError as e:
        logger.warning("Sub-query planning failed (%s); falling back to a single query", e)
        queries = []
    return queries[: settings.max_sub_queries] or [topic]


async def _search_one(query: str) -> list[dict]:
    tool = _tavily_tool()

    @_retrying()
    async def _do():
        return await tool.ainvoke({"query": query})

    try:
        response = await _do()
    except ResearchAgentError:
        raise
    except Exception as e:
        raise SearchProviderError(f"Web search failed for '{query}': {e}") from e

    if isinstance(response, dict):
        return response.get("results", []) or []
    if isinstance(response, list):
        return response
    return []


def _dedupe_results(all_results: list[list[dict]]) -> list[dict]:
    seen_urls: set[str] = set()
    merged: list[dict] = []
    for results in all_results:
        for r in results:
            url = r.get("url", "")
            if url and url in seen_urls:
                continue
            seen_urls.add(url)
            merged.append(r)
    return merged


def create_researcher_agent():
    """Decomposes the topic into a few sub-queries, runs them concurrently
    against Tavily, dedupes by URL, then asks the LLM to extract sourced
    bullets from the merged pool. Returns structured sources alongside the
    prose summary so the frontend can render real citations."""

    async def researcher_invoke(input_dict: dict) -> dict:
        topic = (input_dict.get("input") or "").strip() or "General research information"
        llm_inst = _get_llm(input_dict)

        sub_queries = await _plan_sub_queries(llm_inst, topic)
        logger.info("Researching %r via sub-queries: %s", topic, sub_queries)

        search_results = await asyncio.gather(
            *(_search_one(q) for q in sub_queries), return_exceptions=True
        )

        ok_results: list[list[dict]] = []
        errors: list[str] = []
        for r in search_results:
            if isinstance(r, Exception):
                errors.append(str(r))
            else:
                ok_results.append(r)

        if not ok_results:
            raise SearchProviderError(
                f"All searches failed: {'; '.join(errors) if errors else 'no results'}"
            )

        merged = _dedupe_results(ok_results)[:8]
        sources = [
            Source(title=r.get("title", "Untitled"), url=r.get("url", "")).model_dump()
            for r in merged
            if r.get("url")
        ]

        if not merged:
            raw_output = "No results found"
        else:
            formatted = [
                f"**{r.get('title', 'Untitled')}**\nSource: {r.get('url', 'N/A')}\n"
                f"{(r.get('content') or '')[:400]}"
                for r in merged
            ]
            raw_output = "\n---\n".join(formatted)

        summary_prompt = research_summary_prompt_template.format(topic=topic, raw_output=raw_output)
        try:
            result: ResearchBullets = await _invoke_structured(llm_inst, ResearchBullets, summary_prompt)
            bullets = result.bullets
        except ResearchAgentError as e:
            logger.warning("Summarization failed (%s); using raw snippets as bullets", e)
            bullets = [f"{r.get('title', 'Untitled')}: {(r.get('content') or '')[:200]}" for r in merged[:5]]

        brief = {
            "query": topic,
            "sub_queries": sub_queries,
            "bullets": bullets,
            "sources": sources,
        }
        display_text = "\n".join(f"- {b}" for b in bullets)
        return {"output": display_text, "brief": brief, "input": topic}

    return researcher_invoke


# ─── WRITER ──────────────────────────────────────────────────────────────────


def _format_research_for_prompt(state: dict) -> str:
    if state.get("hitl_approved") and state.get("hitl_edited_findings"):
        return state["hitl_edited_findings"]

    findings = state.get("research_findings", [])
    parts = []
    for f in findings:
        if isinstance(f, dict):
            bullets = "\n".join(f"- {b}" for b in f.get("bullets", []))
            sources = ", ".join(s.get("url", "") for s in f.get("sources", []))
            parts.append(f"{bullets}\nSources: {sources}")
        else:
            parts.append(str(f))
    return "\n\n".join(parts) if parts else "No research available."


def create_writer_chain():
    async def writer_invoke(state: dict) -> str:
        prompt = writer_prompt_template.format(
            main_task=state.get("main_task", ""),
            research_findings=_format_research_for_prompt(state),
            draft=state.get("draft", ""),
            critique_notes=state.get("critique_notes", ""),
        )
        llm_inst = _get_llm(state)
        response = await _invoke(llm_inst, prompt)
        content = response.content if hasattr(response, "content") else str(response)
        if not content or not content.strip():
            raise LLMProviderError("Writer returned an empty draft.")
        return content

    return writer_invoke


# ─── CRITIQUE ────────────────────────────────────────────────────────────────


def create_critique_chain():
    async def critique_invoke(state: dict) -> CritiqueVerdict:
        draft = state.get("draft", "")
        revision_num = state.get("revision_number", 0)
        settings = get_settings()

        if len(draft.strip()) < 100:
            return CritiqueVerdict(approved=False, summary="Draft is too short.", fixes=["Generate a comprehensive report covering all required sections."])

        if revision_num >= settings.max_revisions:
            return CritiqueVerdict(approved=True, summary="Maximum revisions reached; accepting current draft.")

        prompt = critique_prompt_template.format(main_task=state.get("main_task", ""), draft=draft)
        llm_inst = _get_llm(state)
        return await _invoke_structured(llm_inst, CritiqueVerdict, prompt)

    return critique_invoke
