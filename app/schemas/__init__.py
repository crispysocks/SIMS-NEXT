from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentDetail,
    PaginatedStudents,
)
from app.schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherDetail,
    PaginatedTeachers,
)
from app.schemas.class_schema import (
    ClassCreate,
    ClassUpdate,
    ClassDetail,
    PaginatedClasses,
)

__all__ = [
    "StudentCreate",
    "StudentUpdate",
    "StudentDetail",
    "PaginatedStudents",
    "TeacherCreate",
    "TeacherUpdate",
    "TeacherDetail",
    "PaginatedTeachers",
    "ClassCreate",
    "ClassUpdate",
    "ClassDetail",
    "PaginatedClasses",
]