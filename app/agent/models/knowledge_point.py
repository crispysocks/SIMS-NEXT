"""知识点表——三级树结构（章 → 节 → 知识点），parent_id 自引用。"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.core.database import Base


class KnowledgePoint(Base):
    __tablename__ = "agent_knowledge_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("agent_subjects.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("agent_knowledge_points.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)  # 1=章 / 2=节 / 3=知识点
    sort_order = Column(Integer, default=0)
    core_weight = Column(Float, default=1.0)  # 核心权重，用于加权计算掌握率
