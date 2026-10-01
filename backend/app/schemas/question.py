from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Question(BaseModel):
    question_id: str = Field(..., min_length=1)

    subject: str = Field(..., min_length=1)
    topic: Optional[str] = None
    difficulty: Optional[str] = None

    question_type: str = "mcq"

    question: str = Field(..., min_length=1)

    options: List[str] = Field(default_factory=list)

    correct_answer: Optional[str] = None
    explanation: Optional[str] = None

    source: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)