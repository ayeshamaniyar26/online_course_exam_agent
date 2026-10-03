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
from backend.app.agents.question_agent.question_agent import QuestionAgent
from backend.app.graph.error_handler import handle_error, should_retry
from backend.app.graph.openclaw_node import openclaw_node
from backend.app.schemas.agent_state import AgentState
from backend.app.graph.mcp_node import mcp_node
from backend.app.agents.question_generation_agent.question_generation_agent import (
    QuestionGenerationAgent,
)
from backend.app.agents.validation_agent.validation_agent import (
    ValidationAgent,
)


# ============================================================
# COORDINATOR
# ============================================================

coordinator = CoordinatorAgent()
question_agent = QuestionAgent()
question_generation_agent = QuestionGenerationAgent()
validation_agent = ValidationAgent()

def coordinator_node(state: AgentState) -> dict:
    """Run the Coordinator and update shared workflow state."""

    result = coordinator.run(state)

    trace = state.get("trace", [])

    return {
        "current_agent": result["current_agent"],
        "current_stage": result["current_stage"],
        "trace": trace + [result["trace_entry"]],
    }


# ============================================================
# AGENT INTEGRATION POINTS
# ============================================================

def question_generation_node(state: AgentState) -> dict:
    """Run the Question Agent and prepare question retrieval."""

    result = question_agent.run(state)

    trace = state.get("trace", [])

    trace_entry = result.get(
        "trace_entry",
        {
            "agent": "question_agent",
            "action": "question_generation_stage",
        },
    )

    action = result.get("action", {})

    return {
        "current_stage": "question_generation",
        "current_agent": "question_agent",
        "action": action,
        "trace": trace + [trace_entry],
    }


def question_generation_agent_node(state: AgentState) -> dict:
    """Run the Question Generation Agent."""

    result = question_generation_agent.run(state)

    trace = state.get("trace", [])

    return {
        "current_agent": result.get(
            "current_agent",
            "question_generation_agent",
        ),
        "action": result.get("action", {}),
        "questions": result.get(
            "questions",
            state.get("questions", []),
        ),
        "trace": trace + [
            result.get(
                "trace_entry",
                {
                    "agent": "question_generation_agent",
                    "action": "generate_questions",
                },
            )
        ],
    }

def validation_agent_node(state: AgentState) -> dict:
    """Run the Validation Agent on retrieved/generated questions."""

    result = validation_agent.run(state)

    trace = state.get("trace", [])

    return {
        "current_agent": result.get(
            "current_agent",
            "validation_agent",
        ),
        "action": result.get("action", {}),
        "questions": result.get(
            "questions",
            state.get("questions", []),
        ),
        "validation_results": result.get(
            "validation_results",
            [],
        ),
        "trace": trace + [
            result.get(
                "trace_entry",
                {
                    "agent": "validation_agent",
                    "action": "validate_questions",
                },
            )
        ],
    }


def exam_session_node(state: AgentState) -> dict:
    """Integration point for examination/session."""

    return {
        "current_stage": "exam_session",
        "current_agent": "exam_session_agent",
        "trace": state.get("trace", [])
        + [
            {
                "agent": "exam_session_agent",
                "action": "exam_session_stage",
            }
        ],
    }


def evaluation_node(state: AgentState) -> dict:
    """Integration point for evaluation."""

    return {
        "current_stage": "evaluation",
        "current_agent": "evaluation_agent",
        "trace": state.get("trace", [])
        + [
            {
                "agent": "evaluation_agent",
                "action": "evaluation_stage",
            }
        ],
    }


# ============================================================
# ERROR HANDLING
# ============================================================

def error_handler_node(state: AgentState) -> dict:
    """Handle workflow errors."""

    error_message = (
        state.get("last_error")
        or "Unknown workflow error"
    )

    return handle_error(
        state,
        error_message,
    )


# ============================================================
# TERMINAL NODES
# ============================================================

def completed_node(state: AgentState) -> dict:
    """Finish workflow successfully."""

    return {
        "current_stage": "completed",
        "current_agent": "coordinator",
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
    """Finish workflow after unrecoverable error."""

    return {
        "current_stage": "error",
        "current_agent": "error_handler",
        "final_result": {
            "status": "error",
            "errors": state.get("errors", []),
            "last_error": state.get("last_error"),
            "retry_count": state.get("retry_count", 0),
        },
        "trace": state.get("trace", [])
        + [
            {
                "agent": "error_handler",
                "action": "workflow_failed",
            }
        ],
    }


# ============================================================
# COORDINATOR ROUTING
# ============================================================

def route_after_coordinator(
    state: AgentState,
) -> Literal[
    "question_generation",
    "exam_session",
    "evaluation",
    "completed",
    "error",
]:
    """Route according to Coordinator decision."""

    stage = state.get("current_stage")

    if stage in {
        "question_generation",
        "exam_session",
        "evaluation",
        "completed",
        "error",
    }:
        return stage

    return "error"


# ============================================================
# REVISION ROUTING
# ============================================================

def route_after_revision(
    state: AgentState,
) -> Literal[
    "coordinator",
    "error_handler",
    "completed",
]:
    """Decide what happens after revision."""

    revision = state.get("revision", {})

    status = revision.get("status")

    if status == "continue":
        return "coordinator"

    if status == "revise":
        return "error_handler"

    return "completed"


# ============================================================
# ERROR RETRY ROUTING
# ============================================================

def route_after_error(
    state: AgentState,
) -> Literal[
    "reason_and_plan",
    "error",
]:
    """Decide whether workflow should retry."""

    result = should_retry(state)

    if result == "retry":
        return "reason_and_plan"

    return "error"




def route_after_question_retrieval(
    state: AgentState,
) -> Literal[
    "validation",
    "question_generation",
]:
    """Decide whether retrieved questions satisfy the teacher's exact mix."""

    requirements = state.get("requirements", {})
    question_mix = requirements.get("question_mix")

    existing_questions = state.get("questions", [])

    # If the teacher specified a question mix, check each type.
    if question_mix:
        question_type_counts = {
            "normal_mcq": 0,
            "scenario_mcq": 0,
            "coding": 0,
        }

        for question in existing_questions:
            question_type = question.get("question_type")

            if question_type in question_type_counts:
                question_type_counts[question_type] += 1

        mix_satisfied = all(
            question_type_counts[question_type] >= int(required_count)
            for question_type, required_count in question_mix.items()
        )

        if mix_satisfied:
            return "validation"

        return "question_generation"

    # Backward compatibility for older requirement format.
    required_count = requirements.get(
        "count",
        requirements.get("number_of_questions", 5),
    )

    if len(existing_questions) >= required_count:
        return "validation"

    return "question_generation"



# ============================================================
# BUILD EXAM GRAPH
# ============================================================

def build_exam_graph():
    """
    Build the complete Online Course Examination System
    Agentic workflow.

    Flow:

        START
          ↓
       PERCEIVE
          ↓
      COORDINATOR
          ↓
    REASON + PLAN
          ↓
         ACT
          ↓
      OPENCLAW
          ↓
       OBSERVE
          ↓
        REVISE
          ↓
      COORDINATOR
          ↓
       ...
    """

    graph = StateGraph(AgentState)

    # ========================================================
    # CORE AGENTIC NODES
    # ========================================================

    graph.add_node(
        "perceive",
        perceive,
    )

    graph.add_node(
        "coordinator",
        coordinator_node,
    )

    graph.add_node(
        "reason_and_plan",
        reason_and_plan,
    )

    graph.add_node(
        "act",
        act,
    )

    graph.add_node(
        "observe",
        observe,
    )

    graph.add_node(
        "revise",
        revise,
    )

    # ========================================================
    # OPENCLAW RUNTIME NODE
    # ========================================================

    graph.add_node(
        "openclaw",
        openclaw_node,
    )

    # ========================================================
    # AGENT INTEGRATION POINTS
    # ========================================================

    graph.add_node(
        "question_generation",
        question_generation_node,
    )

    graph.add_node("mcp_retrieval", mcp_node)

    graph.add_node(
        "exam_session",
        exam_session_node,
    )

    graph.add_node(
        "evaluation",
        evaluation_node,
    )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    graph.add_node(
        "error_handler",
        error_handler_node,
    )

    # ========================================================
    # TERMINAL NODES
    # ========================================================

    graph.add_node(
        "completed",
        completed_node,
    )

    graph.add_node(
        "error",
        error_node,
    )

    graph.add_node(
        "question_generation_agent",
        question_generation_agent_node,
    )

    graph.add_node(
        "validation",
        validation_agent_node,
    )

    # ========================================================
    # START
    # ========================================================

    graph.add_edge(
        START,
        "perceive",
    )

    # ========================================================
    # PERCEIVE → COORDINATOR
    # ========================================================

    graph.add_edge(
        "perceive",
        "coordinator",
    )

    # ========================================================
    # COORDINATOR ROUTING
    # ========================================================

    graph.add_conditional_edges(
        "coordinator",
        route_after_coordinator,
        {
            "question_generation": "question_generation",
            "exam_session": "exam_session",
            "evaluation": "evaluation",
            "completed": "completed",
            "error": "error_handler",
        },
    )

    # ========================================================
    # AGENT STAGES → AGENTIC LOOP
    # ========================================================

    graph.add_edge(
        "question_generation",
        "mcp_retrieval",
    )

    graph.add_conditional_edges(
        "mcp_retrieval",
        route_after_question_retrieval,
        {
            "validation": "validation",
            "question_generation": "question_generation_agent",
        },
    )

    graph.add_edge(
        "question_generation_agent",
        "validation",
    )

    graph.add_edge(
        "validation",
        "reason_and_plan",
    )

    graph.add_edge(
        "exam_session",
        "reason_and_plan",
    )

    graph.add_edge(
        "evaluation",
        "reason_and_plan",
    )

    # ========================================================
    # AGENTIC LOOP
    #
    # REASON + PLAN
    #        ↓
    #       ACT
    #        ↓
    #    OPENCLAW
    #        ↓
    #     OBSERVE
    #        ↓
    #      REVISE
    # ========================================================

    graph.add_edge(
        "reason_and_plan",
        "act",
    )

    graph.add_edge(
        "act",
        "openclaw",
    )

    graph.add_edge(
        "openclaw",
        "observe",
    )

    graph.add_edge(
        "observe",
        "revise",
    )

    # ========================================================
    # REVISION ROUTING
    # ========================================================

    graph.add_conditional_edges(
        "revise",
        route_after_revision,
        {
            "coordinator": "coordinator",
            "error_handler": "error_handler",
            "completed": "completed",
        },
    )

    # ========================================================
    # ERROR / RETRY ROUTING
    # ========================================================

    graph.add_conditional_edges(
        "error_handler",
        route_after_error,
        {
            "reason_and_plan": "reason_and_plan",
            "error": "error",
        },
    )

    # ========================================================
    # TERMINAL EDGES
    # ========================================================

    graph.add_edge(
        "completed",
        END,
    )

    graph.add_edge(
        "error",
        END,
    )

    # ========================================================
    # COMPILE
    # ========================================================

    return graph.compile()


# ============================================================
# MAIN COMPILED GRAPH
# ============================================================

exam_graph = build_exam_graph()

def create_exam_state(exam_request) -> AgentState:
    """Convert an ExamRequest into the initial AgentState."""

    question_mix = None

    if exam_request.question_mix:
        question_mix = {
            "normal_mcq": exam_request.question_mix.normal_mcq,
            "scenario_mcq": exam_request.question_mix.scenario_mcq,
            "coding": exam_request.question_mix.coding,
        }

    requirements = {
        "subject": exam_request.subject,
        "topic": exam_request.topic,
        "difficulty": exam_request.difficulty,
        "number_of_questions": exam_request.number_of_questions,
    }

    if question_mix:
        requirements["question_mix"] = question_mix

    return {
        "student": exam_request.student.model_dump(),
        "goal": "Generate examination questions",
        "requirements": requirements,
        "questions": [],
        "answers": [],
        "validation_results": [],
        "evaluation_results": [],
        "errors": [],
        "trace": [],
        "iteration_count": 0,
        "retry_count": 0,
    }