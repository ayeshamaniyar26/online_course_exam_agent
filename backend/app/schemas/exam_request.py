from typing import Optional

from pydantic import BaseModel, Field

from .student import Student


class ExamRequest(BaseModel):
    student: Student

    subject: str = Field(..., min_length=1)
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    number_of_questions: int = Field(..., ge=1)
    exam_mode: str = "practice"