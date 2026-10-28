from datetime import datetime, timedelta, timezone

from backend.app.agents.exam_session_agent.exam_session_agent import (
    ExamSessionAgent,
)
from backend.app.schemas.exam_session import ExamSessionStatus


def main():
    agent = ExamSessionAgent()

    questions = [
        {"question_id": "q1"},
        {"question_id": "q2"},
    ]

    session = agent.create_session(
        exam_id="exam-expiry-preserve-test",
        student_id="01FE23BCI001",
        questions=questions,
        duration_minutes=30,
    )

    session = agent.start_session(session)

    # Student answers two questions.
    session = agent.submit_answer(
        session,
        "q1",
        "A",
    )

    session = agent.submit_answer(
        session,
        "q2",
        "SELECT * FROM students",
    )

    print(
        "ANSWERS BEFORE EXPIRY:",
        session.answered_questions,
    )

    # Force the deadline into the past.
    session.ends_at = (
        datetime.now(timezone.utc)
        - timedelta(seconds=1)
    )

    # Expire the session.
    session = agent.expire_session(session)

    print(
        "STATUS AFTER EXPIRY:",
        session.status,
    )

    print(
        "ANSWERS AFTER EXPIRY:",
        session.answered_questions,
    )

    print(
        "SAVED ANSWERS:",
        session.answers,
    )

    print(
        "SUBMITTED AT:",
        session.submitted_at,
    )

    # Verify answers were preserved.
    if (
        session.status == ExamSessionStatus.EXPIRED
        and session.answered_questions == 2
        and "q1" in session.answers
        and "q2" in session.answers
        and session.submitted_at is not None
    ):
        print("AUTO-EXPIRY ANSWER PRESERVATION: PASSED")
    else:
        print("AUTO-EXPIRY ANSWER PRESERVATION: FAILED")


if __name__ == "__main__":
    main()