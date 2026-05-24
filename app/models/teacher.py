from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Index
from app.core.database import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_no = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    entry_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_teacher_no_deleted", "teacher_no", "is_deleted"),
    )