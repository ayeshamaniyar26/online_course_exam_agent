from typing import Any, Dict

from backend.app.schemas.agent_state import AgentState


class QuestionAgent:
    """
    Interface for the Question Agent.

    The Question Agent receives the shared AgentState,
    understands the student's question requirement,
    and prepares the request for question retrieval
    or generation.

    Friend 2 will implement the actual intelligence here.
    """

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Process the current question requirement.

        This method is intentionally kept as an integration
        contract for the real Question Agent.
        """

        requirements = state.get("requirements", {})

        return {
            "current_agent": "question_agent",
            "action": {
                "type": "question_request",
                "requirements": requirements,
            },
            "trace_entry": {
                "agent": "question_agent",
                "action": "process_question_requirement",
            },
        }