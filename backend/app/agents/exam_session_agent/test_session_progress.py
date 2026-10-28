from backend.app.agents.exam_session_agent.exam_session_agent import (
    ExamSessionAgent,
)


def main():
    agent = ExamSessionAgent()

    questions = [
        {"question_id": "q1"},
        {"question_id": "q2"},
        {"question_id": "q3"},
    ]

    session = agent.create_session(
        exam_id="exam-progress",
        student_id="01FE23BCI001",
        questions=questions,
        duration_minutes=30,
    )

    session = agent.start_session(session)

    print("INITIAL PROGRESS:")
    print(agent.get_progress(session))

    session = agent.submit_answer(
        session,
        "q1",
        "A",
    )

    print("\nAFTER Q1 ANSWER:")
    print(agent.get_progress(session))

    current = agent.get_current_question(
        session,
        questions,
    )

    print("\nCURRENT QUESTION:")
    print(current["question_id"])

    next_question = agent.next_question(
        session,
        questions,
    )

    print("\nNEXT QUESTION:")
    print(next_question["question_id"])

    print("\nFINAL PROGRESS:")
    print(agent.get_progress(session))


if __name__ == "__main__":
    main()