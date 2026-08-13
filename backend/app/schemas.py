# app/schemas.py
"""Typed contracts shared across the graph, the LLM structured-output calls,
and the FastAPI layer. Keeping these in one place is what lets the Supervisor
and Critiquer avoid brittle string-matching on LLM output.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ─── LLM structured-output schemas ──────────────────────────────────────────


class SupervisorDecision(BaseModel):
    """Fallback routing decision, only used when deterministic rules in
    agents.py can't decide (see create_supervisor_chain)."""

    next_step: Literal["researcher", "writer", "END"]
    task_description: str = Field(default="Continue work")


class SubQueryPlan(BaseModel):
    """2-4 non-overlapping search angles for a research topic."""

    queries: List[str] = Field(min_length=1, max_length=4)


class ResearchBullets(BaseModel):
    """Sourced factual bullets extracted from search results."""

    bullets: List[str] = Field(min_length=1, max_length=6)


class CritiqueVerdict(BaseModel):
    """Structured critique output — replaces substring-matching on 'APPROVED'."""

    approved: bool
    summary: str = Field(description="One sentence explaining the verdict")
    fixes: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Concrete, scoped fix instructions. Empty when approved.",
    )


# ─── Domain models used inside graph state ──────────────────────────────────


class Source(BaseModel):
    title: str
    url: str


class ResearchBrief(BaseModel):
    """One research cycle's output — stored as a dict in ResearchState so it
    stays trivially JSON-serializable for checkpointing and SSE streaming."""

    query: str
    sub_queries: List[str]
    bullets: List[str]
    sources: List[Source]


# ─── API request/response models ────────────────────────────────────────────


class StartResearchRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    llm_provider: Literal["groq", "ollama"] = "groq"
    llm_model: Optional[str] = None
    ollama_url: Optional[str] = None


class ResumeAction(BaseModel):
    action: Literal["approve", "research"]
    edited_text: Optional[str] = None
    query: Optional[str] = None


class HealthResponse(BaseModel):
    tavily_configured: bool
    groq_configured: bool
    ollama_reachable: bool
