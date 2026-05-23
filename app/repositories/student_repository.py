from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.student import Student


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_student_no(self, student_no: str, include_deleted: bool = False) -> Optional[Student]:
        query = self.db.query(Student).filter(Student.student_no == student_no)
        if not include_deleted:
            query = query.filter(Student.is_deleted == False)
        return query.first()

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Student]:
        query = self.db.query(Student).filter(Student.id == id)
        if not include_deleted:
            query = query.filter(Student.is_deleted == False)
        return query.first()

    def exists_by_student_no(self, student_no: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Student.id).filter(
            and_(
                Student.student_no == student_no,
                Student.is_deleted == False
            )
        )
        if exclude_id:
            query = query.filter(Student.id != exclude_id)
        return query.first() is not None

    def create(self, student: Student) -> Student:
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def update(self, student: Student) -> Student:
        self.db.commit()
        self.db.refresh(student)
        return student

    def soft_delete(self, student: Student) -> None:
        student.is_deleted = True
        self.db.commit()

    def list(
        self,
        skip: int,
        limit: int,
        name: Optional[str] = None,
        student_no: Optional[str] = None,
        class_id: Optional[int] = None
    ) -> tuple[list[Student], int]:
        query = self.db.query(Student).filter(Student.is_deleted == False)

        if name:
            query = query.filter(Student.name.like(f"%{name}%"))
        if student_no:
            query = query.filter(Student.student_no == student_no)
        if class_id:
            query = query.filter(Student.class_id == class_id)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total