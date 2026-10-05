from backend.app.agents.exam_session_agent.exam_session_agent import (
    ExamSessionAgent,
)


def main():
    agent = ExamSessionAgent()

    questions = [
        {"question_id": "q1"},
        {"question_id": "q2"},
    ]

    # Create session
    session = agent.create_session(
        exam_id="exam-001",
        student_id="student-001",
        questions=questions,
        duration_minutes=30,
    )

    # Start session
    session = agent.start_session(session)

    # Submit one answer
    session = agent.submit_answer(
        session,
        "q1",
        "A",
    )

    # Submit the entire exam
    session = agent.submit_session(session)

    print("STATUS:", session.status)
    print("SUBMITTED AT:", session.submitted_at)

    # Try to answer after submission.
    try:
        agent.submit_answer(
            session,
            "q2",
            "B",
        )

        print(
            "ERROR: answer was accepted after submission"
        )

    except ValueError as error:
        print(
            "LOCK TEST PASSED:",
            error,
        )


if __name__ == "__main__":
    main()