from typing import Any, Dict

from backend.app.schemas.agent_state import AgentState


class QuestionAgent:
    """
    Decide how examination questions should be obtained.

    The agent uses teacher-provided requirements such as:
    - subject
    - topic
    - difficulty
    - question mix
    """

    def run(self, state: AgentState) -> Dict[str, Any]:
        requirements = state.get("requirements", {})

        subject = requirements.get("subject")
        difficulty = requirements.get("difficulty", "L1")
        topic = requirements.get("topic")

        if not subject:
            return {
                "current_agent": "question_agent",
                "action": {
                    "type": "question_request",
                    "status": "error",
                    "reason": "Subject is required.",
                },
                "trace_entry": {
                    "agent": "question_agent",
                    "action": "invalid_question_requirement",
                },
            }

        question_mix = requirements.get("question_mix")

        # Backward compatibility with the existing requirement format.
        if not question_mix:
            count = requirements.get(
                "count",
                requirements.get("number_of_questions", 5),
            )

            question_mix = {
                "normal_mcq": count,
                "scenario_mcq": 0,
                "coding": 0,
            }

        total_count = sum(
            int(value)
            for value in question_mix.values()
        )

        existing_questions = state.get("questions", [])

        # Check whether the existing questions satisfy the teacher's
        # exact requested question mix.
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
            return {
                "current_agent": "question_agent",
                "action": {
                    "type": "use_existing_questions",
                    "questions": existing_questions[:total_count],
                    "question_mix": question_mix,
                },
                "trace_entry": {
                    "agent": "question_agent",
                    "action": "use_existing_questions",
                    "question_count": total_count,
                    "question_mix": question_mix,
                },
            }

        retrieval_request = {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "question_mix": question_mix,
            "count": total_count,
        }

        return {
            "current_agent": "question_agent",
            "action": {
                "type": "retrieve_questions",
                "retrieval_request": retrieval_request,
            },
            "trace_entry": {
                "agent": "question_agent",
                "action": "prepare_question_retrieval",
                "requirements": retrieval_request,
            },
        }