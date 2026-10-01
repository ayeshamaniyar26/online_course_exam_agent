from typing import Dict, Any

from backend.app.schemas.agent_state import AgentState


def perceive(state: AgentState) -> Dict[str, Any]:
    """Capture and organize the current situation."""

    requirements = state.get("requirements", {})
    questions = state.get("questions", [])
    answers = state.get("answers", [])

    perception = {
        "goal": state.get("goal", ""),
        "requirements": requirements,
        "question_count": len(questions),
        "answer_count": len(answers),
        "current_stage": state.get("current_stage", ""),
    }

    return {
        "perception": perception,
        "current_agent": "agentic_controller",
        "trace": state.get("trace", [])
        + [
            {
                "stage": "perceive",
                "action": "analyze_current_state",
            }
        ],
    }


def reason_and_plan(state: AgentState) -> Dict[str, Any]:
    """Reason about the current situation and create the next plan."""

    perception = state.get("perception", {})
    current_stage = state.get("current_stage", "")

    if current_stage == "question_generation":
        next_action = "request_questions"

    elif current_stage == "exam_session":
        next_action = "start_exam_session"

    elif current_stage == "evaluation":
        next_action = "evaluate_answers"

    elif current_stage == "completed":
        next_action = "finish"

    else:
        next_action = "coordinate"

    plan = {
        "objective": perception.get("goal", ""),
        "next_action": next_action,
        "reason": f"Selected action based on current stage: {current_stage}",
    }

    return {
        "plan": plan,
        "current_agent": "agentic_controller",
        "trace": state.get("trace", [])
        + [
            {
                "stage": "reason_and_plan",
                "action": next_action,
            }
        ],
    }


def act(state: AgentState) -> Dict[str, Any]:
    """Execute the planned orchestration action."""

    plan = state.get("plan", {})
    next_action = plan.get("next_action", "coordinate")

    action = {
        "action": next_action,
        "status": "requested",
    }

    return {
        "action": action,
        "current_agent": "agentic_controller",
        "trace": state.get("trace", [])
        + [
            {
                "stage": "act",
                "action": next_action,
            }
        ],
    }


def observe(state: AgentState) -> Dict[str, Any]:
    """Observe the result of the previous action."""

    action = state.get("action", {})

    observation = {
        "action": action.get("action"),
        "status": action.get("status"),
        "successful": action.get("status") == "requested",
    }

    return {
        "observation": observation,
        "current_agent": "agentic_controller",
        "trace": state.get("trace", [])
        + [
            {
                "stage": "observe",
                "action": "inspect_action_result",
            }
        ],
    }


def revise(state: AgentState) -> Dict[str, Any]:
    """Decide whether another agentic iteration is required."""

    observation = state.get("observation", {})
    iteration_count = state.get("iteration_count", 0)

    # Safety limit prevents an uncontrolled infinite loop.
    max_iterations = 3

    next_iteration = iteration_count + 1

    if not observation.get("successful"):
        revision_status = "revise"
    elif next_iteration >= max_iterations:
        revision_status = "finish"
    else:
        revision_status = "continue"

    revision = {
        "status": revision_status,
        "iteration": next_iteration,
        "reason": (
            "Maximum test iterations reached."
            if revision_status == "finish"
            else "Continue agentic workflow."
        ),
    }

    return {
        "revision": revision,
        "iteration_count": next_iteration,
        "current_agent": "agentic_controller",
        "trace": state.get("trace", [])
        + [
            {
                "stage": "revise",
                "action": revision_status,
                "iteration": next_iteration,
            }
        ],
    }