from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.teacher import Teacher


class TeacherRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_teacher_no(self, teacher_no: str, include_deleted: bool = False) -> Optional[Teacher]:
        query = self.db.query(Teacher).filter(Teacher.teacher_no == teacher_no)
        if not include_deleted:
            query = query.filter(Teacher.is_deleted == False)
        return query.first()

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Teacher]:
        query = self.db.query(Teacher).filter(Teacher.id == id)
        if not include_deleted:
            query = query.filter(Teacher.is_deleted == False)
        return query.first()

    def exists_by_teacher_no(self, teacher_no: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Teacher.id).filter(
            and_(
                Teacher.teacher_no == teacher_no,
                Teacher.is_deleted == False
            )
        )
        if exclude_id:
            query = query.filter(Teacher.id != exclude_id)
        return query.first() is not None

    def create(self, teacher: Teacher) -> Teacher:
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def update(self, teacher: Teacher) -> Teacher:
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def soft_delete(self, teacher: Teacher) -> None:
        teacher.is_deleted = True
        self.db.commit()

    def list(
        self,
        skip: int,
        limit: int,
        name: Optional[str] = None,
        teacher_no: Optional[str] = None
    ) -> tuple[list[Teacher], int]:
        query = self.db.query(Teacher).filter(Teacher.is_deleted == False)

        if name:
            query = query.filter(Teacher.name.like(f"%{name}%"))
        if teacher_no:
            query = query.filter(Teacher.teacher_no == teacher_no)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total