"""题目-知识点关联表——多对多关联，一个题目可考察多个知识点。"""

from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from app.core.database import Base


class QuestionKnowledgePoint(Base):
    __tablename__ = "agent_question_kps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("agent_questions.id"), nullable=False, index=True)
    kp_id = Column(Integer, ForeignKey("agent_knowledge_points.id"), nullable=False, index=True)
    relevance = Column(Float, default=1.0)  # 题目对该知识点的考察权重 0-1

    __table_args__ = (
        UniqueConstraint("question_id", "kp_id", name="uq_question_kp"),
    )
