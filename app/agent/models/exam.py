"""考试表——记录班级的考试信息。"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date
from app.core.database import Base


class Exam(Base):
    __tablename__ = "agent_exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, nullable=False, index=True)
    class_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)  # "初三(2)班第一次月考"
    exam_date = Column(Date, nullable=False)
    total_score = Column(Integer, nullable=False, default=100)
    exam_type = Column(String(30), nullable=False, default="月考")  # "月考"/"期中"/"期末"/"模拟"
    semester = Column(String(20), nullable=False)  # "2025上"/"2025下"
    created_at = Column(DateTime, default=datetime.utcnow)
