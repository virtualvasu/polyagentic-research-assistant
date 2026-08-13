# app/graph.py

import operator
from typing import Annotated, Any, List, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from app.agents import (
    ResearchAgentError,
    create_critique_chain,
    create_researcher_agent,
    create_supervisor_chain,
    create_writer_chain,
)

# --- 1. Define the State ---


class ResearchState(TypedDict):
    """State for the research workflow."""

    main_task: str
    research_findings: Annotated[List[dict], operator.add]
    draft: str
    critique_notes: str
    critique_approved: bool
    revision_number: int
    next_step: str
    current_sub_task: str
    llm_provider: str
    llm_model: str
    ollama_url: str
    hitl_approved: bool
    hitl_edited_findings: str
    error: str


# --- 2. Initialize Chains and Agents ---

supervisor_chain = create_supervisor_chain()
researcher_agent = create_researcher_agent()
writer_chain = create_writer_chain()
critique_chain = create_critique_chain()


# --- 3. Define Graph Nodes ---


async def supervisor_node(state: ResearchState) -> dict:
    decision = await supervisor_chain(state)
    return {
        "next_step": decision.get("next_step", "researcher"),
        "current_sub_task": decision.get("task_description", "Continue work"),
    }


async def research_node(state: ResearchState) -> dict:
    sub_task = state.get("current_sub_task") or state.get("main_task", "")
    try:
        result = await researcher_agent(
            {
                "input": sub_task,
                "llm_provider": state.get("llm_provider", "groq"),
                "llm_model": state.get("llm_model", ""),
                "ollama_url": state.get("ollama_url", ""),
            }
        )
    except ResearchAgentError as e:
        # Surface the real failure instead of masking it as fake findings —
        # the graph checkpoint from before this node still holds, so the run
        # can be retried without losing prior state.
        return {"error": f"Research failed: {e}"}

    return {"research_findings": [result["brief"]], "error": ""}


async def human_review_node(state: ResearchState) -> dict:
    """Pauses the graph via interrupt() and resumes with whatever the client
    sends through Command(resume=...): {"action": "approve"|"research", ...}.
    """
    findings = state.get("research_findings", [])
    decision = interrupt(
        {
            "type": "research_review",
            "latest_finding": findings[-1] if findings else None,
        }
    )

    action = (decision or {}).get("action")
    if action == "research":
        return {
            "current_sub_task": decision.get("query") or state.get("main_task", ""),
            "next_step": "researcher",
        }

    # Default / "approve"
    return {
        "hitl_approved": True,
        "hitl_edited_findings": decision.get("edited_text", "") if decision else "",
        "next_step": "supervisor",
    }


async def write_node(state: ResearchState) -> dict:
    try:
        draft = await writer_chain(state)
    except ResearchAgentError as e:
        return {"error": f"Writer failed: {e}"}
    return {"draft": draft, "revision_number": state.get("revision_number", 0) + 1, "error": ""}


async def critique_node(state: ResearchState) -> dict:
    try:
        verdict = await critique_chain(state)
    except ResearchAgentError as e:
        return {"error": f"Critique failed: {e}"}

    if verdict.approved:
        notes = f"APPROVED - {verdict.summary}"
    else:
        notes = "\n".join(f"{i}. {fix}" for i, fix in enumerate(verdict.fixes, start=1))

    return {
        "critique_notes": notes,
        "critique_approved": verdict.approved,
        "next_step": "END" if verdict.approved else "writer",
        "error": "",
    }


def _route_after_human_review(state: ResearchState) -> Literal["supervisor", "researcher"]:
    return "researcher" if state.get("next_step") == "researcher" else "supervisor"


def _route_after_supervisor(state: ResearchState) -> Literal["researcher", "writer", "__end__"]:
    step = state.get("next_step", "researcher")
    if step == "END":
        return END
    if step in ("researcher", "writer"):
        return step
    return "researcher"


# --- 4. Build the Graph ---


def build_graph(checkpointer=None):
    """Constructs and compiles the LangGraph workflow. `checkpointer` is
    injected (rather than a module-level singleton) so the FastAPI lifespan
    can own an AsyncSqliteSaver's connection lifecycle, and tests can pass an
    in-memory saver."""

    workflow = StateGraph(ResearchState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", research_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("writer", write_node)
    workflow.add_node("critiquer", critique_node)

    workflow.set_entry_point("supervisor")

    workflow.add_edge("researcher", "human_review")
    workflow.add_edge("writer", "critiquer")
    workflow.add_edge("critiquer", "supervisor")

    workflow.add_conditional_edges(
        "human_review",
        _route_after_human_review,
        {"supervisor": "supervisor", "researcher": "researcher"},
    )
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {"researcher": "researcher", "writer": "writer", END: END},
    )

    return workflow.compile(checkpointer=checkpointer)
