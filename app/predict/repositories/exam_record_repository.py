from sqlalchemy.orm import Session
from app.predict.models.exam_record import ExamRecord
from datetime import datetime

# Import Student to ensure the FK target is resolved
from app.models.student import Student


class ExamRecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_student(self, student_id: int, limit: int = 100) -> list[ExamRecord]:
        return self.db.query(ExamRecord).filter(
            ExamRecord.student_id == student_id,
            ExamRecord.is_deleted == False
        ).order_by(ExamRecord.exam_time.desc()).limit(limit).all()

    def get_by_student_and_subject(self, student_id: int, subject: str) -> list[ExamRecord]:
        return self.db.query(ExamRecord).filter(
            ExamRecord.student_id == student_id,
            ExamRecord.subject == subject,
            ExamRecord.is_deleted == False
        ).order_by(ExamRecord.exam_time.asc()).all()

    def get_latest_by_student(self, student_id: int, limit: int = 20) -> list[ExamRecord]:
        return self.db.query(ExamRecord).filter(
            ExamRecord.student_id == student_id,
            ExamRecord.is_deleted == False
        ).order_by(ExamRecord.exam_time.desc()).limit(limit).all()

    def get_by_exam_name(self, exam_name: str) -> list[ExamRecord]:
        return self.db.query(ExamRecord).filter(
            ExamRecord.exam_name == exam_name,
            ExamRecord.is_deleted == False
        ).all()

    def create(self, data: dict) -> ExamRecord:
        record = ExamRecord(**data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record