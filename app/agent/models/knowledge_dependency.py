"""知识点前置依赖关系——DAG 边表，表示 A 是 B 的前置知识。"""

from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from app.core.database import Base


class KnowledgeDependency(Base):
    __tablename__ = "agent_knowledge_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_kp_id = Column(Integer, ForeignKey("agent_knowledge_points.id"), nullable=False, index=True)
    target_kp_id = Column(Integer, ForeignKey("agent_knowledge_points.id"), nullable=False, index=True)
    dependency_weight = Column(Float, default=1.0)  # 依赖强度 0-1

    __table_args__ = (
        UniqueConstraint("source_kp_id", "target_kp_id", name="uq_kp_dependency"),
    )
