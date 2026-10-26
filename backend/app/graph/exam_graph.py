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
from backend.app.agents.exam_session_agent.exam_session_agent import (
    ExamSessionAgent,
)
from backend.app.schemas.exam_session import (
    ExamSession,
    ExamSessionStatus,
)


# ============================================================
# AGENTS
# ============================================================

coordinator = CoordinatorAgent()
question_agent = QuestionAgent()
question_generation_agent = QuestionGenerationAgent()
validation_agent = ValidationAgent()
exam_session_agent = ExamSessionAgent()


# ============================================================
# COORDINATOR
# ============================================================

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
# QUESTION AGENT
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


# ============================================================
# QUESTION GENERATION AGENT
# ============================================================

def question_generation_agent_node(
    state: AgentState,
) -> dict:
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
        "trace": trace
        + [
            result.get(
                "trace_entry",
                {
                    "agent": "question_generation_agent",
                    "action": "generate_questions",
                },
            )
        ],
    }


# ============================================================
# VALIDATION AGENT
# ============================================================

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
        "trace": trace
        + [
            result.get(
                "trace_entry",
                {
                    "agent": "validation_agent",
                    "action": "validate_questions",
                },
            )
        ],
    }


# ============================================================
# FRIEND 3 — EXAM SESSION
# ============================================================

def exam_session_node(state: AgentState) -> dict:
    """
    Manage the student's examination/practice session.

    Friend 3 responsibilities:
    - create session
    - start session
    - deliver student-safe questions
    - maintain session state
    - maintain answer/progress state

    Important:
    The original validated questions remain in `questions`
    for Friend 4.

    Student-safe questions are stored separately in
    `student_questions`.

    If an existing session is already present in AgentState,
    this node reuses it instead of creating a new session.
    """

    questions = state.get("questions", [])

    if not questions:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "errors": state.get("errors", [])
            + [
                "No validated questions available for exam session."
            ],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "session_failed",
                    "reason": "no_questions",
                }
            ],
        }

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    student = state.get("student", {})
    student_id = student.get("usn")

    if not student_id:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "errors": state.get("errors", [])
            + [
                "Student ID is required to create an exam session."
            ],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "session_failed",
                    "reason": "missing_student_id",
                }
            ],
        }

    # --------------------------------------------------------
    # EXAM ID
    # --------------------------------------------------------

    exam_id = state.get("exam_id")

    if not exam_id:
        exam_id = f"exam-{state.get('run_id', 'session')}"

    # --------------------------------------------------------
    # CHECK FOR EXISTING SESSION
    # --------------------------------------------------------

    existing_session_data = state.get("exam_session")

    if existing_session_data:
        try:
            session = ExamSession.model_validate(
                existing_session_data
            )
        except Exception as exc:
            return {
                "current_stage": "error",
                "current_agent": "exam_session_agent",
                "errors": state.get("errors", [])
                + [
                    f"Invalid existing exam session: {exc}"
                ],
                "trace": state.get("trace", [])
                + [
                    {
                        "agent": "exam_session_agent",
                        "action": "session_failed",
                        "reason": "invalid_existing_session",
                    }
                ],
            }

        # ----------------------------------------------------
        # EXISTING ACTIVE SESSION
        # ----------------------------------------------------

        if session.status == ExamSessionStatus.IN_PROGRESS:
            try:
                safe_questions = exam_session_agent.get_questions(
                    session,
                    questions,
                )
            except ValueError as exc:
                return {
                    "current_stage": "error",
                    "current_agent": "exam_session_agent",
                    "exam_session": session.model_dump(
                        mode="json"
                    ),
                    "errors": state.get("errors", [])
                    + [str(exc)],
                    "trace": state.get("trace", [])
                    + [
                        {
                            "agent": "exam_session_agent",
                            "action": "session_failed",
                            "reason": "active_session_delivery_failed",
                        }
                    ],
                }

            answers = [
                answer.model_dump(mode="json")
                for answer in session.answers.values()
            ]

            progress = exam_session_agent.get_progress(
                session
            )

            return {
                "exam_id": session.exam_id,
                "current_stage": "exam_session",
                "current_agent": "exam_session_agent",
                "exam_session": session.model_dump(
                    mode="json"
                ),
                "questions": questions,
                "student_questions": safe_questions,
                "answers": answers,
                "action": {
                    "type": "session_reused",
                    "session_id": session.session_id,
                    "status": session.status.value,
                    "progress": progress,
                },
                "trace": state.get("trace", [])
                + [
                    {
                        "agent": "exam_session_agent",
                        "action": "session_reused",
                        "session_id": session.session_id,
                        "exam_id": session.exam_id,
                        "question_count": len(
                            safe_questions
                        ),
                        "status": session.status.value,
                    }
                ],
            }

        # ----------------------------------------------------
        # EXISTING SUBMITTED / EXPIRED SESSION
        # ----------------------------------------------------

        if session.status in {
            ExamSessionStatus.SUBMITTED,
            ExamSessionStatus.EXPIRED,
        }:
            answers = [
                answer.model_dump(mode="json")
                for answer in session.answers.values()
            ]

            progress = exam_session_agent.get_progress(
                session
            )

            return {
                "exam_id": session.exam_id,
                "current_stage": "exam_session",
                "current_agent": "exam_session_agent",
                "exam_session": session.model_dump(
                    mode="json"
                ),
                "questions": questions,
                "student_questions": state.get(
                    "student_questions",
                    [],
                ),
                "answers": answers,
                "action": {
                    "type": "session_completed",
                    "session_id": session.session_id,
                    "status": session.status.value,
                    "progress": progress,
                },
                "trace": state.get("trace", [])
                + [
                    {
                        "agent": "exam_session_agent",
                        "action": "session_completed",
                        "session_id": session.session_id,
                        "exam_id": session.exam_id,
                        "status": session.status.value,
                        "answered_questions": (
                            session.answered_questions
                        ),
                    }
                ],
            }

        # ----------------------------------------------------
        # UNKNOWN SESSION STATUS
        # ----------------------------------------------------

        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "errors": state.get("errors", [])
            + [
                "Exam session has an unsupported status."
            ],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "session_failed",
                    "reason": "unsupported_session_status",
                    "status": session.status.value,
                }
            ],
        }

    # --------------------------------------------------------
    # CREATE NEW SESSION
    # --------------------------------------------------------

    session = exam_session_agent.create_session(
        exam_id=exam_id,
        student_id=student_id,
        questions=questions,
        duration_minutes=30,
    )

    # --------------------------------------------------------
    # START SESSION
    # --------------------------------------------------------

    session = exam_session_agent.start_session(
        session
    )

    # --------------------------------------------------------
    # STUDENT-SAFE QUESTIONS
    # --------------------------------------------------------

    safe_questions = exam_session_agent.get_questions(
        session,
        questions,
    )

    # --------------------------------------------------------
    # CONVERT ANSWERS FOR AGENT STATE
    # --------------------------------------------------------

    answers = [
        answer.model_dump(mode="json")
        for answer in session.answers.values()
    ]

    progress = exam_session_agent.get_progress(
        session
    )

    # --------------------------------------------------------
    # RETURN UPDATED LANGGRAPH STATE
    # --------------------------------------------------------

    return {
        "exam_id": exam_id,
        "current_stage": "exam_session",
        "current_agent": "exam_session_agent",

        # Complete session state.
        "exam_session": session.model_dump(
            mode="json"
        ),

        # Keep original validated questions unchanged.
        "questions": questions,

        # Student-facing questions only.
        "student_questions": safe_questions,

        # Currently empty, but ready for student answers.
        "answers": answers,

        # Useful information for downstream nodes/UI.
        "action": {
            "type": "session_started",
            "session_id": session.session_id,
            "status": session.status.value,
            "progress": progress,
        },

        "trace": state.get("trace", [])
        + [
            {
                "agent": "exam_session_agent",
                "action": "session_started",
                "session_id": session.session_id,
                "exam_id": exam_id,
                "question_count": len(
                    safe_questions
                ),
                "status": session.status.value,
            }
        ],
    }


# ============================================================
# FRIEND 3 — ANSWER SUBMISSION
# ============================================================

def answer_submission_node(state: AgentState) -> dict:
    """
    Store pending student answers in the active exam session.

    This node does NOT evaluate correctness. Friend 4 handles
    evaluation after the exam is submitted.
    """

    session_data = state.get("exam_session")

    if not session_data:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "errors": state.get("errors", [])
            + ["Cannot submit answers without an exam session."],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "answer_submission_failed",
                    "reason": "missing_exam_session",
                }
            ],
        }

    try:
        session = ExamSession.model_validate(session_data)
    except Exception as exc:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "errors": state.get("errors", [])
            + [f"Invalid exam session: {exc}"],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "answer_submission_failed",
                    "reason": "invalid_exam_session",
                }
            ],
        }

    pending_answers = state.get("pending_answers", [])
    questions = state.get("questions", [])

    if not pending_answers:
        return {
            "current_stage": "exam_session",
            "current_agent": "exam_session_agent",
            "action": {
                "type": "no_answers_to_submit",
                "session_id": session.session_id,
            },
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "no_answers_to_submit",
                }
            ],
        }

    valid_question_ids = {
        question.get("question_id")
        for question in questions
        if question.get("question_id")
    }

    for item in pending_answers:
        if not isinstance(item, dict):
            raise ValueError(
                "Each pending answer must be a dictionary."
            )

        question_id = item.get("question_id")

        if not question_id:
            raise ValueError(
                "Each pending answer requires question_id."
            )

        if question_id not in valid_question_ids:
            raise ValueError(
                f"Unknown question_id: {question_id}"
            )

    try:
        exam_session_agent.submit_answers(
            session=session,
            answers=pending_answers,
        )
    except ValueError as exc:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "exam_session": session.model_dump(mode="json"),
            "errors": state.get("errors", []) + [str(exc)],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "answer_submission_failed",
                    "reason": str(exc),
                }
            ],
        }

    serialized_answers = [
        answer.model_dump(mode="json")
        for answer in session.answers.values()
    ]

    progress = exam_session_agent.get_progress(session)

    return {
        "exam_session": session.model_dump(mode="json"),
        "answers": serialized_answers,
        "pending_answers": [],
        "current_stage": "exam_session",
        "current_agent": "exam_session_agent",
        "action": {
            "type": "answers_submitted",
            "session_id": session.session_id,
            "answer_count": len(pending_answers),
            "progress": progress,
        },
        "trace": state.get("trace", [])
        + [
            {
                "agent": "exam_session_agent",
                "action": "answers_submitted",
                "session_id": session.session_id,
                "answer_count": len(pending_answers),
                "answered_questions": session.answered_questions,
                "total_questions": session.total_questions,
            }
        ],
    }


# ============================================================
# FRIEND 3 — EXAM SUBMISSION
# ============================================================

def submit_exam_node(state: AgentState) -> dict:
    """
    Submit and lock the current exam session.

    No scoring happens here. The submitted questions, answers and
    session are passed to the Friend 4 evaluation stage.
    """

    session_data = state.get("exam_session")

    if not session_data:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "errors": state.get("errors", [])
            + ["Cannot submit exam without an exam session."],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "exam_submission_failed",
                    "reason": "missing_exam_session",
                }
            ],
        }

    try:
        session = ExamSession.model_validate(session_data)
    except Exception as exc:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "errors": state.get("errors", [])
            + [f"Invalid exam session: {exc}"],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "exam_submission_failed",
                    "reason": "invalid_exam_session",
                }
            ],
        }

    try:
        session = exam_session_agent.submit_session(session)
    except ValueError as exc:
        return {
            "current_stage": "error",
            "current_agent": "exam_session_agent",
            "exam_session": session.model_dump(mode="json"),
            "errors": state.get("errors", []) + [str(exc)],
            "trace": state.get("trace", [])
            + [
                {
                    "agent": "exam_session_agent",
                    "action": "exam_submission_failed",
                    "reason": str(exc),
                }
            ],
        }

    serialized_answers = [
        answer.model_dump(mode="json")
        for answer in session.answers.values()
    ]

    progress = exam_session_agent.get_progress(session)

    return {
        "exam_session": session.model_dump(mode="json"),
        "answers": serialized_answers,
        "pending_answers": [],
        "current_stage": "evaluation",
        "current_agent": "evaluation_agent",
        "action": {
            "type": "exam_submitted",
            "session_id": session.session_id,
            "status": session.status.value,
            "progress": progress,
        },
        "trace": state.get("trace", [])
        + [
            {
                "agent": "exam_session_agent",
                "action": "exam_submitted",
                "session_id": session.session_id,
                "status": session.status.value,
                "answer_count": len(session.answers),
            }
        ],
    }

# ============================================================
# EVALUATION
# ============================================================

def evaluation_node(state: AgentState) -> dict:
    """
    Integration point for Friend 4 evaluation.

    Friend 4 will receive:
    - original questions
    - student answers
    - exam session information
    """

    return {
        "current_stage": "evaluation",
        "current_agent": "evaluation_agent",
        "trace": state.get("trace", [])
        + [
            {
                "agent": "evaluation_agent",
                "action": "evaluation_stage",
                "question_count": len(
                    state.get("questions", [])
                ),
                "answer_count": len(
                    state.get("answers", [])
                ),
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
    "answer_submission",
    "submit_exam",
    "evaluation",
    "completed",
    "error",
]:
    """Route according to Coordinator decision."""

    # Explicit session actions take priority over the coordinator's
    # normal stage decision. This allows a caller to submit answers
    # or submit the exam through the same LangGraph entry point.
    if state.get("pending_answers"):
        return "answer_submission"

    if state.get("submit_exam") is True:
        return "submit_exam"

    stage = state.get("current_stage")

    if stage in {
        "question_generation",
        "exam_session",
        "answer_submission",
        "submit_exam",
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


# ============================================================
# QUESTION RETRIEVAL ROUTING
# ============================================================

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
            question_type_counts[question_type]
            >= int(required_count)
            for question_type, required_count
            in question_mix.items()
        )

        if mix_satisfied:
            return "validation"

        return "question_generation"

    required_count = requirements.get(
        "count",
        requirements.get(
            "number_of_questions",
            5,
        ),
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
    # OPENCLAW
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

    graph.add_node(
        "mcp_retrieval",
        mcp_node,
    )

    graph.add_node(
        "question_generation_agent",
        question_generation_agent_node,
    )

    graph.add_node(
        "validation",
        validation_agent_node,
    )

    graph.add_node(
        "exam_session",
        exam_session_node,
    )

    graph.add_node(
        "answer_submission",
        answer_submission_node,
    )

    graph.add_node(
        "submit_exam",
        submit_exam_node,
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
            "answer_submission": "answer_submission",
            "submit_exam": "submit_exam",
            "evaluation": "evaluation",
            "completed": "completed",
            "error": "error_handler",
        },
    )

    # ========================================================
    # QUESTION PIPELINE
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

    # ========================================================
    # FRIEND 3 — SESSION
    # ========================================================

    graph.add_edge(
        "exam_session",
        "reason_and_plan",
    )

    graph.add_edge(
        "answer_submission",
        "exam_session",
    )

    graph.add_edge(
        "submit_exam",
        "evaluation",
    )

    # ========================================================
    # FRIEND 4 — EVALUATION
    # ========================================================

    graph.add_edge(
        "evaluation",
        "reason_and_plan",
    )

    # ========================================================
    # AGENTIC LOOP
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

    return graph.compile()


# ============================================================
# COMPILED GRAPH
# ============================================================

exam_graph = build_exam_graph()


# ============================================================
# INITIAL AGENT STATE
# ============================================================

def create_exam_state(exam_request) -> AgentState:
    """Convert an ExamRequest into the initial AgentState."""

    question_mix = None

    if exam_request.question_mix:
        question_mix = {
            "normal_mcq": (
                exam_request.question_mix.normal_mcq
            ),
            "scenario_mcq": (
                exam_request.question_mix.scenario_mcq
            ),
            "coding": (
                exam_request.question_mix.coding
            ),
        }

    requirements = {
        "subject": exam_request.subject,
        "topic": exam_request.topic,
        "difficulty": exam_request.difficulty,
        "number_of_questions": (
            exam_request.number_of_questions
        ),
    }

    if question_mix:
        requirements["question_mix"] = question_mix

    return {
        "run_id": f"run-{__import__('uuid').uuid4()}",
        "student": exam_request.student.model_dump(),
        "exam_id": None,
        "exam_session": {},
        "goal": "Generate examination questions",
        "requirements": requirements,
        "questions": [],
        "student_questions": [],
        "answers": [],
        "pending_answers": [],
        "submit_exam": False,
        "validation_results": [],
        "evaluation_results": [],
        "final_result": None,
        "errors": [],
        "trace": [],
        "iteration_count": 0,
        "retry_count": 0,
    }