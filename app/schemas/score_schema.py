from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ScoreCreate(BaseModel):
    student_no: str = Field(..., min_length=1, max_length=20, description="学号")
    exam_name: str = Field(..., min_length=1, max_length=100, description="考试名称")
    score: float = Field(..., ge=0, description="成绩（>=0）")


class ScoreUpdate(BaseModel):
    exam_name: Optional[str] = Field(None, min_length=1, max_length=100)
    score: Optional[float] = Field(None, ge=0)


class ScoreDetail(BaseModel):
    id: int
    student_no: str
    student_name: str
    exam_name: str
    score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedScores(BaseModel):
    items: list[ScoreDetail]
    total: int