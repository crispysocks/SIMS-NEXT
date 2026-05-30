"""会话表——每个用户 + 班级组合可创建多个会话，支持历史和恢复。"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    class_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False, default="新对话")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
