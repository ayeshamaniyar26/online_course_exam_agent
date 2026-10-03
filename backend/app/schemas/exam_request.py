from typing import Optional

from pydantic import BaseModel, Field

from backend.app.schemas.student import Student


class QuestionMix(BaseModel):
    normal_mcq: int = Field(default=0, ge=0)
    scenario_mcq: int = Field(default=0, ge=0)
    coding: int = Field(default=0, ge=0)


class ExamRequest(BaseModel):
    student: Student
    subject: str = Field(..., min_length=1)
    topic: Optional[str] = None
    difficulty: Optional[str] = None

    number_of_questions: int = Field(..., ge=1)

    question_mix: Optional[QuestionMix] = None

    exam_mode: str = "practice"