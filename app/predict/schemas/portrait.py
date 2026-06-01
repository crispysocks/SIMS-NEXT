from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StudentPortraitBase(BaseModel):
    learning_type: Optional[str] = None
    science_ability: Optional[str] = None  # 强/中/弱
    english_ability: Optional[str] = None
    improvement_potential: Optional[str] = None  # 高/中/低


class StudentPortraitDetail(StudentPortraitBase):
    student_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class RiskWarning(BaseModel):
    risk_level: str  # 高/中/低
    risk_tags: list[str]