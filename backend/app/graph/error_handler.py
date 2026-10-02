from typing import Any, Dict

from backend.app.schemas.agent_state import AgentState


DEFAULT_MAX_RETRIES = 3


def handle_error(state: AgentState, error_message: str) -> Dict[str, Any]:
    """
    Record an error and determine whether the workflow should retry
    or terminate.
    """

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", DEFAULT_MAX_RETRIES)

    next_retry_count = retry_count + 1

    errors = list(state.get("errors", []))
    errors.append(error_message)

    if next_retry_count <= max_retries:
        status = "retry"
        next_stage = "reason_and_plan"
    else:
        status = "failed"
        next_stage = "error"

    return {
        "retry_count": next_retry_count,
        "max_retries": max_retries,
        "last_error": error_message,
        "errors": errors,
        "current_stage": next_stage,
        "trace": state.get("trace", [])
        + [
            {
                "stage": "error_handler",
                "status": status,
                "retry_count": next_retry_count,
                "error": error_message,
            }
        ],
    }


def validation_failed(
    state: AgentState,
    validation_error: str,
) -> Dict[str, Any]:
    """
    Route a validation failure back into the agentic
    reasoning/re-planning cycle.
    """

    return handle_error(state, validation_error)


def should_retry(state: AgentState) -> str:
    """
    Determine the next routing decision after an error.
    """

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", DEFAULT_MAX_RETRIES)

    if retry_count < max_retries:
        return "retry"

    return "error"