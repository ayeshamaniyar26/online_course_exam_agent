from backend.app.agents.exam_session_agent.exam_session_agent import (
    ExamSessionAgent,
)


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
            # Sensitive fields that must NOT reach the student.
            "correct_answer": "A",
            "expected_answer": "SELECT",
            "explanation": "SELECT retrieves data.",
            "source": "internal-question-bank",
            "metadata": {
                "answer_key": "A",
                "internal_id": "secret-123",
            },
        },
        {
            "question_id": "q2",
            "subject": "Programming",
            "topic": "SQL",
            "difficulty": "medium",
            "question_type": "coding",
            "question": "Write a query to select all students.",
            "options": {},
            "correct_answer": "SELECT * FROM students",
            "expected_answer": "SELECT * FROM students",
            "explanation": "This selects every student.",
            "source": "internal-question-bank",
            "metadata": {
                "answer_key": "SELECT * FROM students",
            },
        },
    ]

    session = agent.create_session(
        exam_id="exam-student-safety-test",
        student_id="01FE23BCI001",
        questions=questions,
        duration_minutes=30,
    )

    session = agent.start_session(session)

    student_questions = agent.get_questions(
        session,
        questions,
    )

    forbidden_fields = {
        "correct_answer",
        "expected_answer",
        "explanation",
        "source",
        "metadata",
    }

    print("STUDENT QUESTIONS:")
    print(student_questions)
    print()

    for question in student_questions:
        leaked_fields = forbidden_fields.intersection(
            question.keys()
        )

        assert not leaked_fields, (
            f"Sensitive fields leaked for "
            f"{question.get('question_id')}: {leaked_fields}"
        )

        assert "question_id" in question
        assert "question" in question
        assert "options" in question

    print("FORBIDDEN FIELDS:")
    print(forbidden_fields)
    print()

    print("STUDENT-SAFE DELIVERY TEST PASSED")


if __name__ == "__main__":
    main()
