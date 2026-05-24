from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.score_model import Score


def _escape_like(s: str) -> str:
    """Escape special characters for SQL LIKE patterns"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ScoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Score]:
        query = self.db.query(Score).filter(Score.id == id)
        if not include_deleted:
            query = query.filter(Score.is_deleted == False)
        return query.first()

    def create(self, score_obj: Score) -> Score:
        self.db.add(score_obj)
        self.db.commit()
        self.db.refresh(score_obj)
        return score_obj

    def update(self, score_obj: Score) -> Score:
        self.db.commit()
        self.db.refresh(score_obj)
        return score_obj

    def soft_delete(self, score_obj: Score) -> None:
        score_obj.is_deleted = True
        self.db.commit()

    def list(
        self,
        student_no: Optional[str] = None,
        exam_name: Optional[str] = None,
        student_name: Optional[str] = None
    ) -> list[Score]:
        query = self.db.query(Score).filter(Score.is_deleted == False)

        if student_no:
            query = query.filter(Score.student_no == student_no)
        if exam_name:
            query = query.filter(Score.exam_name.like(f"%{_escape_like(exam_name)}%", escape="\\"))
        if student_name:
            query = query.filter(Score.student_name.like(f"%{_escape_like(student_name)}%", escape="\\"))

        return query.all()