from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Index
from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_no = Column(String(20), nullable=False, index=True)
    student_name = Column(String(100), nullable=False)
    exam_name = Column(String(100), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_student_no_deleted", "student_no", "is_deleted"),
        Index("idx_exam_name_deleted", "exam_name", "is_deleted"),
    )