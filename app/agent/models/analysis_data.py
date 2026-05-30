"""分析数据存储——Tool 返回的完整结构化数据，支持跨会话缓存复用。"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from app.core.database import Base


class AnalysisData(Base):
    __tablename__ = "agent_analysis_data"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("agent_sessions.id"), nullable=False)
    tool_name = Column(String(50), nullable=False)
    cache_key = Column(String(200), nullable=False, index=True)
    data_json = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
