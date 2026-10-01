from typing import Dict, Any

from backend.app.schemas.agent_state import AgentState


class CoordinatorAgent:
    """
    Coordinates the overall agentic examination workflow.

    The Coordinator does not generate questions or evaluate answers.
    It decides which stage/agent should act next based on the current state.
    """

    def decide_next_stage(self, state: AgentState) -> str:
        """
        Decide the next stage of the workflow from the current AgentState.
        """

        # Stop if a previous error requires handling.
        if state.get("errors"):
            return "error"

        # If no questions exist yet, request question generation/retrieval.
        if not state.get("questions"):
            return "question_generation"

        # If questions exist but there are no answers yet,
        # move to the examination/session stage.
        if not state.get("answers"):
            return "exam_session"

        # If answers exist but evaluation has not happened,
        # move to evaluation.
        if not state.get("evaluation_results"):
            return "evaluation"

        # Everything required has been completed.
        return "completed"

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute one Coordinator decision and return the updated routing information.
        """

        next_stage = self.decide_next_stage(state)

        return {
            "current_agent": "coordinator",
            "current_stage": next_stage,
            "trace_entry": {
                "agent": "coordinator",
                "action": "route",
                "next_stage": next_stage,
            },
        }