from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.class_model import Class


def _escape_like(s: str) -> str:
    """Escape special characters for SQL LIKE patterns"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ClassRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Class]:
        query = self.db.query(Class).filter(Class.id == id)
        if not include_deleted:
            query = query.filter(Class.is_deleted == False)
        return query.first()

    def get_by_class_no(self, class_no: str, include_deleted: bool = False) -> Optional[Class]:
        query = self.db.query(Class).filter(Class.class_no == class_no)
        if not include_deleted:
            query = query.filter(Class.is_deleted == False)
        return query.first()

    def exists_by_class_no(self, class_no: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Class.id).filter(
            and_(
                Class.class_no == class_no,
                Class.is_deleted == False
            )
        )
        if exclude_id:
            query = query.filter(Class.id != exclude_id)
        return query.first() is not None

    def exists_by_head_teacher_no(self, head_teacher_no: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Class.id).filter(
            and_(
                Class.head_teacher_no == head_teacher_no,
                Class.is_deleted == False
            )
        )
        if exclude_id:
            query = query.filter(Class.id != exclude_id)
        return query.first() is not None

    def create(self, class_obj: Class) -> Class:
        self.db.add(class_obj)
        self.db.commit()
        self.db.refresh(class_obj)
        return class_obj

    def update(self, class_obj: Class) -> Class:
        self.db.commit()
        self.db.refresh(class_obj)
        return class_obj

    def soft_delete(self, class_obj: Class) -> None:
        class_obj.is_deleted = True
        self.db.commit()

    def list(
        self,
        class_no: Optional[str] = None,
        class_name: Optional[str] = None
    ) -> list[Class]:
        query = self.db.query(Class).filter(Class.is_deleted == False)

        if class_no:
            query = query.filter(Class.class_no.like(f"%{_escape_like(class_no)}%", escape="\\"))
        if class_name:
            query = query.filter(Class.class_name.like(f"%{_escape_like(class_name)}%", escape="\\"))

        return query.all()