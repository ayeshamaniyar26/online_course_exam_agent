from typing import Any


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

    This is the MCP tool that will later be called by
    the OpenClaw/LangGraph agent.
    """

    # Temporary implementation.
    # Later this will read your actual JSON question banks.

    return {
        "success": True,
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "count": count,
        "questions": [],
        "source": "question_bank",
    }


# ============================================================
# QUESTION VALIDATION TOOL
# ============================================================

def validate_question(question: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the basic structure of an examination question.
    """

    required_fields = [
        "question",
        "options",
        "correct",
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

    if not isinstance(options, list) or len(options) < 2:
        return {
            "valid": False,
            "reason": "Question must contain at least two options.",
        }

    if question["correct"] not in options:
        return {
            "valid": False,
            "reason": "Correct answer must exist in options.",
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