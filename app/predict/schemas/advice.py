from pydantic import BaseModel
from typing import Optional


class SubjectAdvice(BaseModel):
    subject: str
    advice: str
    expected_improvement: str  # "+18分"


class AIAdvice(BaseModel):
    current_tier: str
    target_tier: str
    suggestions: list[SubjectAdvice]
    overall_expected_improvement: str