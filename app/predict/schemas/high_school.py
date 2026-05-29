from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class HighSchoolBase(BaseModel):
    school_name: str = Field(..., min_length=1, max_length=100)
    school_level: str = Field(..., pattern="^(L1|L2|L3|L4)$")
    region: str = Field(..., min_length=1, max_length=50)
    annual_admission_count: int = Field(..., gt=0)


class HighSchoolCreate(HighSchoolBase):
    pass


class HighSchoolDetail(HighSchoolBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HighSchoolList(BaseModel):
    items: list[HighSchoolDetail]
    total: int