"""消息表——只存 user 和 assistant 两种角色，Tool 数据在 tool_calls 表。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("agent_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
