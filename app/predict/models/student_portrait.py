from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from app.core.database import Base


class StudentPortrait(Base):
    __tablename__ = "student_portraits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True, unique=True)
    overall_score = Column(Float, nullable=False, default=0.0)
    subject_strengths = Column(Text, nullable=True)  # JSON string
    subject_weaknesses = Column(Text, nullable=True)  # JSON string
    trend = Column(String(20), nullable=True)  # rising, stable, declining
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)