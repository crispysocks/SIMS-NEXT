"""考试数据访问层——考试 CRUD。"""

from sqlalchemy.orm import Session
from app.agent.models.exam import Exam


class ExamRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_by_class(self, class_id: int, subject_id: int | None = None) -> list[dict]:
        """获取某班级的所有考试记录。"""
        q = self.db.query(Exam).filter(Exam.class_id == class_id)
        if subject_id is not None:
            q = q.filter(Exam.subject_id == subject_id)
        rows = q.order_by(Exam.exam_date.asc()).all()
        return [
            {"id": r.id, "name": r.name, "exam_date": str(r.exam_date),
             "exam_type": r.exam_type, "semester": r.semester,
             "total_score": r.total_score}
            for r in rows
        ]

    def get_by_id(self, exam_id: int) -> dict | None:
        r = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not r:
            return None
        return {
            "id": r.id, "name": r.name, "exam_date": str(r.exam_date),
            "exam_type": r.exam_type, "semester": r.semester,
            "total_score": r.total_score, "class_id": r.class_id,
            "subject_id": r.subject_id,
        }

    def get_by_ids(self, exam_ids: list[int]) -> list[dict]:
        rows = self.db.query(Exam).filter(Exam.id.in_(exam_ids)).order_by(Exam.exam_date.asc()).all()
        return [
            {"id": r.id, "name": r.name, "exam_date": str(r.exam_date),
             "exam_type": r.exam_type, "semester": r.semester}
            for r in rows
        ]

    def create(self, class_id: int, subject_id: int, name: str,
               exam_date, exam_type: str = "月考", semester: str = "2025上",
               total_score: int = 100) -> Exam:
        exam = Exam(
            class_id=class_id,
            subject_id=subject_id,
            name=name,
            exam_date=exam_date,
            exam_type=exam_type,
            semester=semester,
            total_score=total_score,
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        return exam
