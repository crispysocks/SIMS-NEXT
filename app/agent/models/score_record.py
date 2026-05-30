"""成绩记录表——学生在一道题目上的得分。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.core.database import Base


class ScoreRecord(Base):
    __tablename__ = "agent_score_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_no = Column(String(20), nullable=False, index=True)  # 关联现有 students 表
    exam_id = Column(Integer, ForeignKey("agent_exams.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("agent_questions.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 实际得分
    max_score = Column(Integer, nullable=False)  # 题目满分（冗余，加速计算）
    created_at = Column(DateTime, default=datetime.utcnow)
