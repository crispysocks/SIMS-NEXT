from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from app.core.database import Base


class StudentPortrait(Base):
    __tablename__ = "student_portraits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True, unique=True)
    learning_type = Column(String(20), nullable=True)  # 稳定型, 波动型, 退步型
    science_ability = Column(String(10), nullable=True)
    english_ability = Column(String(10), nullable=True)
    improvement_potential = Column(String(10), nullable=True)
    current_tier = Column(String(20), nullable=True)
    target_tier = Column(String(20), nullable=True)
    risk_tags = Column(Text, nullable=True)  # JSON string
    overall_score = Column(Float, nullable=False, default=0.0)
    subject_strengths = Column(Text, nullable=True)  # JSON string
    subject_weaknesses = Column(Text, nullable=True)  # JSON string
    trend = Column(String(20), nullable=True)  # rising, stable, declining
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)