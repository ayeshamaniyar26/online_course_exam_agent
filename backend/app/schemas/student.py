from pydantic import BaseModel, Field


class Student(BaseModel):
    roll_number: int = Field(..., ge=1)
    usn: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    division: str = Field(..., min_length=1)