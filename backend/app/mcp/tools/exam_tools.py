from typing import Any

from backend.app.agents.question_agent.question_bank_loader import (
    QuestionBankLoader,
)


question_bank_loader = QuestionBankLoader()

# ============================================================
# QUESTION BANK TOOLS
# ============================================================

def get_question_bank(
    subject: str,
    topic: str | None = None,
    difficulty: str | None = None,
    count: int = 5,
) -> dict[str, Any]:
    """
    Retrieve questions from the examination question bank.

    Questions are loaded from the project's JSON question banks
    through QuestionBankLoader.
    """

    if count < 1:
        return {
            "success": False,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "count": count,
            "questions": [],
            "source": "question_bank",
            "error": "Count must be at least 1.",
        }

    try:
        # If difficulty is specified, load only that level.
        if difficulty:
            questions = question_bank_loader.load_questions(
                subject=subject,
                difficulty=difficulty,
                topic=topic,
                count=count,
            )

        # If difficulty is not specified, search all three levels.
        else:
            questions = []

            for level in ["L1", "L2", "L3"]:
                remaining = count - len(questions)

                if remaining <= 0:
                    break

                level_questions = question_bank_loader.load_questions(
                    subject=subject,
                    difficulty=level,
                    topic=topic,
                    count=remaining,
                )

                questions.extend(level_questions)

        return {
            "success": True,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "count": len(questions),
            "questions": questions,
            "source": "question_bank",
        }

    except FileNotFoundError as error:
        return {
            "success": False,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "count": 0,
            "questions": [],
            "source": "question_bank",
            "error": str(error),
        }


# ============================================================
# QUESTION VALIDATION TOOL
# ============================================================

def validate_question(question: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the structure of an examination question
    using the project's actual JSON question format.
    """

    required_fields = [
        "question",
        "options",
        "correct_answer",
        "explanation",
    ]

    missing = [
        field
        for field in required_fields
        if field not in question
    ]

    if missing:
        return {
            "valid": False,
            "missing_fields": missing,
        }

    options = question.get("options")
    correct_answer = question.get("correct_answer")

    # The question bank stores options as:
    # {"A": "...", "B": "...", "C": "...", "D": "..."}
    if not isinstance(options, dict):
        return {
            "valid": False,
            "reason": "Options must be a dictionary containing answer choices.",
        }

    if len(options) < 2:
        return {
            "valid": False,
            "reason": "Question must contain at least two options.",
        }

    if correct_answer not in options:
        return {
            "valid": False,
            "reason": "Correct answer must match one of the option keys.",
        }

    if not isinstance(question.get("question"), str) or not question["question"].strip():
        return {
            "valid": False,
            "reason": "Question text cannot be empty.",
        }

    if not isinstance(question.get("explanation"), str) or not question["explanation"].strip():
        return {
            "valid": False,
            "reason": "Explanation cannot be empty.",
        }

    return {
        "valid": True,
        "reason": "Question passed validation.",
    }


# ============================================================
# SAVE QUESTION TOOL
# ============================================================

def save_question(question: dict[str, Any]) -> dict[str, Any]:
    """
    Save a validated question.

    Actual JSON/database persistence will be connected later.
    """

    validation = validate_question(question)

    if not validation["valid"]:
        return {
            "success": False,
            "saved": False,
            "validation": validation,
        }

    return {
        "success": True,
        "saved": True,
        "question": question,
    }


# ============================================================
# EXAM REQUIREMENTS TOOL
# ============================================================

def get_exam_requirements(
    subject: str,
    difficulty: str,
    count: int,
) -> dict[str, Any]:
    """
    Return normalized examination requirements.
    """

    return {
        "success": True,
        "requirements": {
            "subject": subject,
            "difficulty": difficulty,
            "count": count,
        },
    }


# ============================================================
# SUBJECT/TOPIC TOOL
# ============================================================

def get_subject_topics(subject: str) -> dict[str, Any]:
    """
    Return available topics for a subject.
    """

    topics = {
        "CN": [
            "OSI Model",
            "TCP/IP",
            "Routing",
            "Transport Layer",
            "Application Layer",
        ],
        "DBMS": [
            "Normalization",
            "Transactions",
            "SQL",
            "Indexing",
            "ER Model",
        ],
        "OOPS": [
            "Inheritance",
            "Polymorphism",
            "Encapsulation",
            "Abstraction",
        ],
        "OS": [
            "Process Management",
            "CPU Scheduling",
            "Deadlocks",
            "Memory Management",
        ],
    }

    return {
        "success": True,
        "subject": subject,
        "topics": topics.get(subject.upper(), []),
    }