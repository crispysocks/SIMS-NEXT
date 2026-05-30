"""题目表——关联考试和题型。"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.core.database import Base


class Question(Base):
    __tablename__ = "agent_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("agent_exams.id"), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    question_type = Column(String(30), nullable=False)  # "选择题"/"填空题"/"解答题"/"证明题"
    difficulty = Column(Float, nullable=False)  # 预设难度系数 0-1
    max_score = Column(Integer, nullable=False)
    sort_order = Column(Integer, default=0)  # 在试卷中的题号
