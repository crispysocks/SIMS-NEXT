from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey
from app.core.database import Base


class ExamRecord(Base):
    __tablename__ = "exam_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    student_no = Column(String(20), nullable=False)
    exam_name = Column(String(100), nullable=False)
    subject = Column(String(50), nullable=False)
    score = Column(Integer, nullable=False)
    ranking = Column(Integer, nullable=True)
    exam_time = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)