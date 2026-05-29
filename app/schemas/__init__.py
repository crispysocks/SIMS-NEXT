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
from app.schemas.score_schema import (
    ScoreCreate,
    ScoreUpdate,
    ScoreDetail,
    PaginatedScores,
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenData,
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
    "ScoreCreate",
    "ScoreUpdate",
    "ScoreDetail",
    "PaginatedScores",
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenData",
]