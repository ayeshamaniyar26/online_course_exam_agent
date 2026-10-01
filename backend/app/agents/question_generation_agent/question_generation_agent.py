from typing import Any, Dict

from backend.app.schemas.agent_state import AgentState


class QuestionGenerationAgent:
    """
    Interface for the Question Generation Agent.

    This agent will later use the appropriate LLM/skills
    to generate questions when retrieval is insufficient
    or when new questions are required.

    Friend 2 will implement the actual generation logic.
    """

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Prepare the question-generation request.
        """

        requirements = state.get("requirements", {})

        return {
            "current_agent": "question_generation_agent",
            "action": {
                "type": "generate_questions",
                "requirements": requirements,
            },
            "trace_entry": {
                "agent": "question_generation_agent",
                "action": "prepare_question_generation",
            },
        }