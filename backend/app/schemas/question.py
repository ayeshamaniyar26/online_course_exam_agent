from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Question(BaseModel):
    question_id: Optional[str] = None

    subject: str = Field(..., min_length=1)
    topic: Optional[str] = None
    difficulty: Optional[str] = None

    question_type: str = "normal_mcq"

    question: str = Field(..., min_length=1)

    # MCQ questions use A/B/C/D keys.
    # Coding questions use an empty dictionary.
    options: Dict[str, str] = Field(default_factory=dict)

    correct_answer: Optional[str] = None

    # Used for coding/SQL questions.
    expected_answer: Optional[str] = None

    explanation: Optional[str] = None

    source: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)