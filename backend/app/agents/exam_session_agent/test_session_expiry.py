from datetime import datetime, timedelta, timezone

from backend.app.agents.exam_session_agent.exam_session_agent import (
    ExamSessionAgent,
)


def main():
    agent = ExamSessionAgent()

    questions = [
        {"question_id": "q1"},
    ]

    session = agent.create_session(
        exam_id="exam-expiry-test",
        student_id="student-001",
        questions=questions,
        duration_minutes=30,
    )

    session = agent.start_session(session)

    print("INITIAL STATUS:", session.status)
    print("ORIGINAL END:", session.ends_at)

    # Force the deadline into the past for testing.
    session.ends_at = (
        datetime.now(timezone.utc)
        - timedelta(seconds=1)
    )

    print("FORCED END:", session.ends_at)

    # Try submitting an answer after the deadline.
    try:
        agent.submit_answer(
            session,
            "q1",
            "A",
        )

        print(
            "ERROR: answer was accepted after expiry"
        )

    except ValueError as error:
        print(
            "EXPIRY TEST PASSED:",
            error,
        )

    print("FINAL STATUS:", session.status)


if __name__ == "__main__":
    main()