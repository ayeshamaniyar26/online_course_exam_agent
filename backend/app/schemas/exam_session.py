from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ExamSessionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


class StudentAnswer(BaseModel):
    question_id: str = Field(..., min_length=1)
    answer: str = ""
    answered_at: Optional[datetime] = None


class ExamSession(BaseModel):
    session_id: str = Field(..., min_length=1)
    exam_id: str = Field(..., min_length=1)
    student_id: str = Field(..., min_length=1)

    status: ExamSessionStatus = ExamSessionStatus.NOT_STARTED

    started_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None

    current_question_index: int = Field(default=0, ge=0)

    # Question IDs belonging to this exam session.
    # We store IDs only, not the actual questions.
    question_ids: List[str] = Field(default_factory=list)

    answers: Dict[str, StudentAnswer] = Field(default_factory=dict)

    total_questions: int = Field(default=0, ge=0)

    answered_questions: int = Field(default=0, ge=0)