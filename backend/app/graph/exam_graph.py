from typing import Literal

from langgraph.graph import END, START, StateGraph

from backend.app.agents.coordinator.coordinator_agent import CoordinatorAgent
from backend.app.graph.agentic_loop import (
    act,
    observe,
    perceive,
    reason_and_plan,
    revise,
)
from backend.app.schemas.agent_state import AgentState


coordinator = CoordinatorAgent()


def coordinator_node(state: AgentState) -> dict:
    """Run the Coordinator and update the shared workflow state."""

    result = coordinator.run(state)

    trace = state.get("trace", [])
    trace.append(result["trace_entry"])

    return {
        "current_agent": result["current_agent"],
        "current_stage": result["current_stage"],
        "trace": trace,
    }


def question_generation_node(state: AgentState) -> dict:
    """Temporary integration point for Friend 2's Question Agent."""

    return {
        "current_stage": "question_generation",
        "trace": state.get("trace", [])
        + [
            {
                "agent": "question_stage",
                "action": "awaiting_question_agent",
            }
        ],
    }


def exam_session_node(state: AgentState) -> dict:
    """Temporary integration point for the examination/session implementation."""

    return {
        "current_stage": "exam_session",
        "trace": state.get("trace", [])
        + [
            {
                "agent": "exam_session",
                "action": "awaiting_session_implementation",
            }
        ],
    }


def evaluation_node(state: AgentState) -> dict:
    """Temporary integration point for the evaluation implementation."""

    return {
        "current_stage": "evaluation",
        "trace": state.get("trace", [])
        + [
            {
                "agent": "evaluation",
                "action": "awaiting_evaluation_implementation",
            }
        ],
    }


def completed_node(state: AgentState) -> dict:
    """Finish the workflow."""

    return {
        "current_stage": "completed",
        "final_result": {
            "status": "completed",
        },
        "trace": state.get("trace", [])
        + [
            {
                "agent": "coordinator",
                "action": "workflow_completed",
            }
        ],
    }


def error_node(state: AgentState) -> dict:
    """Handle workflow errors."""

    return {
        "current_stage": "error",
        "final_result": {
            "status": "error",
            "errors": state.get("errors", []),
        },
    }


def route_after_coordinator(
    state: AgentState,
) -> Literal[
    "question_generation",
    "exam_session",
    "evaluation",
    "completed",
    "error",
]:
    return state["current_stage"]


def route_after_revision(
    state: AgentState,
) -> Literal[
    "coordinator",
    "completed",
]:
    """Decide whether the agentic cycle should continue."""

    revision = state.get("revision", {})

    if revision.get("status") == "continue":
        return "coordinator"

    return "completed"


def build_exam_graph():
    """Build the integrated agentic examination graph."""

    graph = StateGraph(AgentState)

    # Core orchestration nodes
    graph.add_node("perceive", perceive)
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("reason_and_plan", reason_and_plan)
    graph.add_node("act", act)
    graph.add_node("observe", observe)
    graph.add_node("revise", revise)

    # Current integration points
    graph.add_node("question_generation", question_generation_node)
    graph.add_node("exam_session", exam_session_node)
    graph.add_node("evaluation", evaluation_node)

    # Final states
    graph.add_node("completed", completed_node)
    graph.add_node("error", error_node)

    # Main agentic cycle
    graph.add_edge(START, "perceive")
    graph.add_edge("perceive", "coordinator")

    graph.add_conditional_edges(
        "coordinator",
        route_after_coordinator,
        {
            "question_generation": "reason_and_plan",
            "exam_session": "reason_and_plan",
            "evaluation": "reason_and_plan",
            "completed": "completed",
            "error": "error",
        },
    )

    graph.add_edge("reason_and_plan", "act")
    graph.add_edge("act", "observe")
    graph.add_edge("observe", "revise")

    # Revision decides whether another cycle is needed.
    graph.add_conditional_edges(
        "revise",
        route_after_revision,
        {
            "coordinator": "coordinator",
            "completed": "completed",
        },
    )

    graph.add_edge("completed", END)
    graph.add_edge("error", END)

    return graph.compile()


exam_graph = build_exam_graph()