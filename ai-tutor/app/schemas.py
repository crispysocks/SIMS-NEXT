from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request ────────────────────────────────────────────────────────────────────

class AnswerSubmission(BaseModel):
    student_answer: str = Field(description="Free-text math expression, e.g. '3', '-1,-4', '2*x+3'")


# ── Response ───────────────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    difficulty: str
    question_text: str
    # answer is intentionally excluded — never send correct answer to client


class AnswerResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_correct: bool
    correct_answer: str
    student_answer: str
    topic: str
    tutor_response: Optional["TutorResponseOut"] = None


class TutorResponseOut(BaseModel):
    explanation: str
    hint: str
    encouragement: str


class HintResponse(BaseModel):
    hint: str
    level: int
    remaining: int


class MasteryStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic_id: str
    alpha: float
    beta: float
    total_attempts: int
    correct_attempts: int
    last_seen: Optional[datetime] = None
    mastery: float
    variance: float


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mastery_states: list[MasteryStateOut]
    total_questions: int
    correct_count: int
    accuracy: float
    correct_streak: int
    wrong_streak: int
