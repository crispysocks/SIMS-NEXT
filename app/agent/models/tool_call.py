"""Tool 调用记录——一次 tool 调用一条记录，关联到 assistant message。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.core.database import Base


class ToolCall(Base):
    __tablename__ = "agent_tool_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("agent_messages.id"), nullable=False, index=True)
    tool_name = Column(String(50), nullable=False)
    params_json = Column(JSON, nullable=False)
    summary = Column(String(500), nullable=True)
    data_id = Column(String(36), nullable=True)
    error = Column(String(500), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
