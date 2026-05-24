from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional


class ClassBase(BaseModel):
    class_no: str = Field(..., min_length=1, max_length=50, description="班级编号")
    class_name: str = Field(..., min_length=1, max_length=100, description="班级名称")
    head_teacher_no: str = Field(..., min_length=6, max_length=20, description="班主任工号")


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    class_no: Optional[str] = Field(None, min_length=1, max_length=50)
    class_name: Optional[str] = Field(None, min_length=1, max_length=100)
    head_teacher_no: Optional[str] = Field(None, min_length=6, max_length=20)


class ClassDetail(ClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedClasses(BaseModel):
    items: list[ClassDetail]
    total: int