from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.student_repository import StudentRepository
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate, StudentDetail, PaginatedStudents


class StudentService:
    def __init__(self, db: Session):
        self.repo = StudentRepository(db)

    def create_student(self, data: StudentCreate) -> StudentDetail:
        if self.repo.exists_by_student_no(data.student_no):
            raise ValueError(f"学号 {data.student_no} 已存在")

        student = Student(
            student_no=data.student_no,
            name=data.name,
            gender=data.gender,
            age=data.age,
            native_place=data.native_place,
            class_id=data.class_id,
            enrollment_date=data.enrollment_date,
        )
        created = self.repo.create(student)
        return StudentDetail.model_validate(created)

    def get_student(self, student_no: str) -> StudentDetail:
        student = self.repo.get_by_student_no(student_no)
        if not student:
            raise ValueError(f"学生 {student_no} 不存在")
        return StudentDetail.model_validate(student)

    def list_students(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        student_no: Optional[str] = None,
        class_id: Optional[int] = None
    ) -> PaginatedStudents:
        skip = (page - 1) * page_size
        students, total = self.repo.list(skip, page_size, name, student_no, class_id)
        return PaginatedStudents(
            items=[StudentDetail.model_validate(s) for s in students],
            total=total,
            page=page,
            page_size=page_size
        )

    def update_student(self, student_no: str, data: StudentUpdate) -> StudentDetail:
        student = self.repo.get_by_student_no(student_no)
        if not student:
            raise ValueError(f"学生 {student_no} 不存在")

        if data.student_no and data.student_no != student_no:
            if self.repo.exists_by_student_no(data.student_no, exclude_id=student.id):
                raise ValueError(f"学号 {data.student_no} 已存在")
            student.student_no = data.student_no

        update_data = data.model_dump(exclude_unset=True, exclude={"student_no"})
        for key, value in update_data.items():
            if value is not None:
                setattr(student, key, value)

        updated = self.repo.update(student)
        return StudentDetail.model_validate(updated)

    def delete_student(self, student_no: str) -> None:
        student = self.repo.get_by_student_no(student_no)
        if not student:
            raise ValueError(f"学生 {student_no} 不存在")
        self.repo.soft_delete(student)