from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class StudentBase(BaseModel):
    student_no: str = Field(..., min_length=6, max_length=20, description="学号，字母开头+数字")
    name: str = Field(..., min_length=2, max_length=20, description="姓名")
    gender: str = Field(..., description="性别")
    age: int = Field(..., ge=6, le=100, description="年龄")
    native_place: Optional[str] = Field(None, max_length=100, description="籍贯")
    class_id: Optional[int] = Field(None, description="班级ID")
    enrollment_date: date = Field(..., description="入学时间")

    @field_validator("student_no")
    @classmethod
    def validate_student_no(cls, v: str) -> str:
        if not v[0].isalpha():
            raise ValueError("学号必须以字母开头")
        if not v.isalnum():
            raise ValueError("学号只能包含字母和数字")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("男", "女"):
            raise ValueError("性别只能为男或女")
        return v


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=20)
    gender: Optional[str] = None
    age: Optional[int] = Field(None, ge=6, le=100)
    native_place: Optional[str] = Field(None, max_length=100)
    class_id: Optional[int] = None
    enrollment_date: Optional[date] = None
    student_no: Optional[str] = Field(None, min_length=6, max_length=20)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("男", "女"):
            raise ValueError("性别只能为男或女")
        return v

    @field_validator("student_no")
    @classmethod
    def validate_student_no(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v[0].isalpha():
                raise ValueError("学号必须以字母开头")
            if not v.isalnum():
                raise ValueError("学号只能包含字母和数字")
        return v


class StudentDetail(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedStudents(BaseModel):
    items: list[StudentDetail]
    total: int
    page: int
    page_size: int