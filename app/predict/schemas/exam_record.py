from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ExamRecordBase(BaseModel):
    student_id: int
    student_no: str = Field(..., min_length=1, max_length=20)
    exam_name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=50)
    score: float = Field(..., ge=0)
    ranking: Optional[int] = Field(None, ge=1)
    exam_time: datetime


class ExamRecordCreate(ExamRecordBase):
    pass


class ExamRecordDetail(ExamRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExamRecordList(BaseModel):
    items: list[ExamRecordDetail]
    total: int