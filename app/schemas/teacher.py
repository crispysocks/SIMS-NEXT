from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TeacherBase(BaseModel):
    teacher_no: str = Field(..., min_length=6, max_length=20, description="工号，字母开头+数字")
    name: str = Field(..., min_length=2, max_length=20, description="姓名")
    gender: str = Field(..., description="性别")
    entry_date: date = Field(..., description="入职时间")

    @field_validator("teacher_no")
    @classmethod
    def validate_teacher_no(cls, v: str) -> str:
        if not v or not v[0].isalpha():
            raise ValueError("工号必须以字母开头")
        if not v.isalnum():
            raise ValueError("工号只能包含字母和数字")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("男", "女"):
            raise ValueError("性别只能为男或女")
        return v


class TeacherCreate(TeacherBase):
    pass


class TeacherUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=20)
    gender: Optional[str] = None
    entry_date: Optional[date] = None
    teacher_no: Optional[str] = Field(None, min_length=6, max_length=20)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("男", "女"):
            raise ValueError("性别只能为男或女")
        return v

    @field_validator("teacher_no")
    @classmethod
    def validate_teacher_no(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or not v[0].isalpha():
                raise ValueError("工号必须以字母开头")
            if not v.isalnum():
                raise ValueError("工号只能包含字母和数字")
        return v


class TeacherDetail(TeacherBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedTeachers(BaseModel):
    items: list[TeacherDetail]
    total: int
    page: int
    page_size: int