"""学生数据访问层——复用现有 Student 模型做关联查询。"""

from sqlalchemy.orm import Session
from app.models.student import Student


class StudentRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_by_class(self, class_id: int) -> list[dict]:
        """获取某班级所有学生。"""
        rows = (
            self.db.query(Student)
            .filter(Student.class_id == class_id)
            .order_by(Student.student_no.asc())
            .all()
        )
        return [
            {"student_no": r.student_no, "name": r.name,
             "gender": r.gender, "class_id": r.class_id}
            for r in rows
        ]

    def get_by_no(self, student_no: str) -> dict | None:
        r = self.db.query(Student).filter(Student.student_no == student_no).first()
        if not r:
            return None
        return {"student_no": r.student_no, "name": r.name, "gender": r.gender}

    def get_class_student_nos(self, class_id: int) -> list[str]:
        """获取某班级所有学生的学号列表。"""
        rows = (
            self.db.query(Student.student_no)
            .filter(Student.class_id == class_id)
            .all()
        )
        return [r.student_no for r in rows]
