import json
from pathlib import Path
from typing import Any


class QuestionBankLoader:
    """
    Loads and filters questions from the project's JSON question banks.

    Supported subjects:
        - DBMS
        - OOPS

    Supported difficulties:
        - L1
        - L2
        - L3
    """

    def __init__(self):
        # Project root:
        # online_course_exam_agent/
        self.project_root = Path(__file__).resolve().parents[4]

        self.question_bank_root = (
            self.project_root / "data" / "question_bank"
        )

    def load_questions(
        self,
        subject: str,
        difficulty: str,
        topic: str | None = None,
        count: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Load questions matching subject, difficulty and optionally topic.
        """

        subject = subject.strip().lower()
        difficulty = difficulty.strip().upper()

        file_path = (
            self.question_bank_root
            / subject
            / f"{subject.upper()}_{difficulty}_100_questions.json"
        )

        if not file_path.exists():
            raise FileNotFoundError(
                f"Question bank not found: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as file:
            questions = json.load(file)

        # Assign stable IDs before filtering by topic.
        for index, question in enumerate(questions, start=1):
            question.setdefault(
                "question_id",
                f"{subject.upper()}_{difficulty}_{index:03d}",
            )

        if topic:
            topic_lower = topic.strip().lower()

            questions = [
                question
                for question in questions
                if question.get("topic", "").strip().lower()
                == topic_lower
            ]

                # Assign stable question IDs without modifying the JSON files.
        for index, question in enumerate(questions, start=1):
            question.setdefault(
                "question_id",
                f"{subject.upper()}_{difficulty}_{index:03d}",
            )

        if count is not None:
            questions = questions[:count]

        return questions