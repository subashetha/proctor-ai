from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ExamCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300, example="Python Fundamentals")
    duration: int = Field(..., gt=0, example=60, description="Exam duration in minutes")

    class Config:
        json_schema_extra = {
            "example": {"title": "Python Fundamentals", "duration": 60}
        }


class ExamResponse(BaseModel):
    id: int
    title: str
    duration: int

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    user_name: str = Field(..., min_length=1, example="alice")
    answers: Dict[str, str] = Field(
        ...,
        example={"q1": "print('hello')", "q2": "print('hello')"},
        description="Map of question_id → answer text"
    )
    time_taken_seconds: Optional[int] = Field(
        None, ge=0, example=1800,
        description="How many seconds the candidate spent on the exam"
    )
    paste_detected: Optional[bool] = Field(
        False,
        description="Frontend flag: did browser detect a paste event?"
    )
    tab_switch_count: Optional[int] = Field(
        0, ge=0,
        description="Number of times candidate switched tabs or lost window focus"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "alice",
                "answers": {"q1": "def foo(): pass", "q2": "def foo(): pass"},
                "time_taken_seconds": 30,
                "paste_detected": True
            }
        }


class SubmissionResponse(BaseModel):
    id: int
    exam_id: int
    user_name: str
    suspicious: bool
    flag_reasons: List[str] = []
    time_taken_seconds: Optional[int]
    audit_log: Optional[str] = None

    class Config:
        from_attributes = True


class SuspiciousFlag(BaseModel):
    reason: str
