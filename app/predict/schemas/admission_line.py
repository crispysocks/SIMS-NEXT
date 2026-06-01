from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class AdmissionLineBase(BaseModel):
    school_id: int
    year: int
    admission_score: float
    admission_rank: int
    student_count: int


class AdmissionLineCreate(AdmissionLineBase):
    pass


class AdmissionLineDetail(AdmissionLineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScoreLinePrediction(BaseModel):
    school_name: str
    last_year_score: float
    predicted_score: float
    fluctuation: str  # "+6" or "-3"


class ScoreLinePredictionList(BaseModel):
    items: list[ScoreLinePrediction]
    total: int