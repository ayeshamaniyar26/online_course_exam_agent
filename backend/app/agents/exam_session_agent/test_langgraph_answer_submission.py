from backend.app.graph.exam_graph import (
    answer_submission_node,
    submit_exam_node,
)
from backend.app.agents.exam_session_agent.exam_session_agent import (
    ExamSessionAgent,
)
from backend.app.schemas.agent_state import AgentState


def main():
    agent = ExamSessionAgent()

    questions = [
        {
            "question_id": "q1",
            "subject": "Database",
            "topic": "SQL",
            "difficulty": "easy",
            "question_type": "normal_mcq",
            "question": "Which SQL command retrieves data?",
            "options": {
                "A": "SELECT",
                "B": "DELETE",
                "C": "DROP",
                "D": "UPDATE",
            },
            "correct_answer": "A",
            "explanation": "SELECT retrieves rows.",
            "source": "test",
            "metadata": {"internal": True},
        },
        {
            "question_id": "q2",
            "subject": "Database",
            "topic": "SQL",
            "difficulty": "medium",
            "question_type": "coding",
            "question": "Write a query that selects all students.",
            "options": {},
            "expected_answer": "SELECT * FROM students",
            "explanation": "The query selects every row.",
            "source": "test",
            "metadata": {"internal": True},
        },
    ]

    session = agent.create_session(
        exam_id="exam-langgraph-answer-test",
        student_id="01FE23BCI001",
        questions=questions,
        duration_minutes=30,
    )

    session = agent.start_session(session)

    state: AgentState = {
        "run_id": "run-langgraph-answer-test",
        "student": {
            "student_id": "01FE23BCI001",
        },
        "exam_id": session.exam_id,
        "exam_session": session.model_dump(mode="json"),
        "questions": questions,
        "student_questions": agent.get_questions(
            session,
            questions,
        ),
        "answers": [],
        "pending_answers": [
            {
                "question_id": "q1",
                "answer": "A",
            },
            {
                "question_id": "q2",
                "answer": "SELECT * FROM students",
            },
        ],
        "validation_results": [],
        "evaluation_results": [],
        "errors": [],
        "trace": [],
        "iteration_count": 0,
        "retry_count": 0,
    }

    print("INITIAL SESSION STATUS:")
    print(session.status)
    print()

    print("PENDING ANSWERS:")
    print(state["pending_answers"])
    print()

    # --------------------------------------------------------
    # ANSWER SUBMISSION NODE
    # --------------------------------------------------------

    answer_result = answer_submission_node(state)

    print("ANSWER SUBMISSION RESULT:")
    print(answer_result["action"])
    print()

    submitted_answers = answer_result["answers"]

    assert len(submitted_answers) == 2, (
        "Expected two saved answers."
    )

    saved_question_ids = {
        answer["question_id"]
        for answer in submitted_answers
    }

    assert saved_question_ids == {"q1", "q2"}, (
        "Saved answer question IDs are incorrect."
    )

    assert answer_result["pending_answers"] == [], (
        "Pending answers should be cleared after submission."
    )

    updated_session = answer_result["exam_session"]

    assert updated_session["status"] == "in_progress", (
        "Session should remain active after answer submission."
    )

    assert updated_session["answered_questions"] == 2, (
        "Expected two answered questions."
    )

    print("SAVED ANSWERS:")
    print(submitted_answers)
    print()

    print(
        "ANSWER SUBMISSION NODE TEST PASSED"
    )
    print()

    # --------------------------------------------------------
    # EXAM SUBMISSION NODE
    # --------------------------------------------------------

    submit_state: AgentState = {
        **state,
        **answer_result,
        "pending_answers": [],
    }

    exam_result = submit_exam_node(submit_state)

    print("EXAM SUBMISSION RESULT:")
    print(exam_result["action"])
    print()

    final_session = exam_result["exam_session"]

    assert final_session["status"] == "submitted", (
        "Exam session should be SUBMITTED."
    )

    assert final_session["submitted_at"] is not None, (
        "Submitted session must have submitted_at."
    )

    assert len(exam_result["answers"]) == 2, (
        "Answers must be preserved after exam submission."
    )

    assert exam_result["current_stage"] == "evaluation", (
        "Submitted exam must hand off to evaluation."
    )

    assert exam_result["current_agent"] == "evaluation_agent", (
        "Submitted exam must target evaluation_agent."
    )

    print("FINAL STATUS:")
    print(final_session["status"])
    print()

    print("ANSWERS AFTER EXAM SUBMISSION:")
    print(exam_result["answers"])
    print()

    print(
        "FRIEND 4 HANDOFF READY:"
    )
    print(
        exam_result["current_stage"],
        "->",
        exam_result["current_agent"],
    )
    print()

    print(
        "LANGGRAPH ANSWER SUBMISSION TEST PASSED"
    )


if __name__ == "__main__":
    main()
