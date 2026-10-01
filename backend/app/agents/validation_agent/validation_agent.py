from typing import Any, Dict

from backend.app.schemas.agent_state import AgentState


class ValidationAgent:
    """
    Interface for the Validation Agent.

    This agent will later validate retrieved/generated questions
    for correctness, completeness, difficulty, duplicates,
    formatting, and other required quality checks.

    Friend 2 will implement the actual validation logic.
    """

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Prepare the question-validation request.
        """

        questions = state.get("questions", [])

        return {
            "current_agent": "validation_agent",
            "action": {
                "type": "validate_questions",
                "question_count": len(questions),
            },
            "trace_entry": {
                "agent": "validation_agent",
                "action": "prepare_question_validation",
            },
        }