"""会话管理——创建/恢复/归档会话，消息存储与查询。"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.agent.models.session import AgentSession
from app.agent.models.chat_message import ChatMessage
from app.agent.models.tool_call import ToolCall
from app.agent.models.analysis_data import AnalysisData


class SessionManager:
    """管理 Agent 会话的生命周期。

    会话绑定 user_id + class_id，支持:
    - 新建会话
    - 恢复历史会话（含完整消息记录）
    - 归档会话
    - 存储/查询 analysis_data（跨会话缓存）
    """

    def __init__(self, db: Session):
        self.db = db

    # Session CRUD

    def create_session(self, user_id: int, class_id: int, title: str = "新对话") -> AgentSession:
        session = AgentSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            class_id=class_id,
            title=title,
            status="active",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> AgentSession | None:
        return self.db.query(AgentSession).filter(
            AgentSession.id == session_id, AgentSession.status == "active"
        ).first()

    def list_sessions(self, user_id: int) -> list[AgentSession]:
        return self.db.query(AgentSession).filter(
            AgentSession.user_id == user_id,
            AgentSession.status == "active",
        ).order_by(AgentSession.updated_at.desc()).all()

    def archive_session(self, session_id: str) -> None:
        session = self.get_session(session_id)
        if session:
            session.status = "archived"
            self.db.commit()

    def update_title(self, session_id: str, title: str) -> None:
        session = self.get_session(session_id)
        if session:
            session.title = title[:200]
            self.db.commit()

    # Message CRUD

    def add_message(self, session_id: str, role: str, content_json: dict) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content_json=content_json)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        self.db.query(AgentSession).filter(AgentSession.id == session_id).update(
            {"updated_at": datetime.utcnow()}
        )
        self.db.commit()
        return msg

    def get_messages(self, session_id: str, limit: int = 20) -> list[ChatMessage]:
        """获取最近 N 条消息（用于构建 LLM 上下文）。"""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()[::-1]

    def get_all_messages(self, session_id: str) -> list[ChatMessage]:
        """获取全部消息（用于恢复历史会话）。"""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()

    # Tool Call

    def add_tool_call(
        self,
        message_id: int,
        tool_name: str,
        params: dict,
        summary: str,
        data_id: str | None = None,
        error: str | None = None,
        duration_ms: int | None = None,
    ) -> ToolCall:
        tc = ToolCall(
            message_id=message_id,
            tool_name=tool_name,
            params_json=params,
            summary=summary,
            data_id=data_id,
            error=error,
            duration_ms=duration_ms,
        )
        self.db.add(tc)
        self.db.commit()
        self.db.refresh(tc)
        return tc

    def get_tool_calls(self, message_id: int) -> list[ToolCall]:
        return self.db.query(ToolCall).filter(ToolCall.message_id == message_id).all()

    # Analysis Data

    def store_analysis_data(
        self, session_id: str, tool_name: str, cache_key: str, data: dict
    ) -> AnalysisData:
        ad = AnalysisData(
            id=str(uuid.uuid4()),
            session_id=session_id,
            tool_name=tool_name,
            cache_key=cache_key,
            data_json=data,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        self.db.add(ad)
        self.db.commit()
        self.db.refresh(ad)
        return ad

    def get_analysis_data(self, data_id: str) -> AnalysisData | None:
        return self.db.query(AnalysisData).filter(
            AnalysisData.id == data_id,
            AnalysisData.expires_at > datetime.utcnow(),
        ).first()

    def find_cached_data(self, cache_key: str) -> AnalysisData | None:
        """按 cache_key 查找未过期的缓存数据（跨会话复用）。"""
        return self.db.query(AnalysisData).filter(
            AnalysisData.cache_key == cache_key,
            AnalysisData.expires_at > datetime.utcnow(),
        ).first()

    # Stream Tokens (内存)

    _stream_store: dict[str, dict] = {}

    def create_stream(self, session_id: str, user_message: str) -> str:
        """创建临时 stream token，存储待处理的用户输入。"""
        stream_id = str(uuid.uuid4())[:8]
        self._stream_store[stream_id] = {
            "session_id": session_id,
            "user_message": user_message,
            "created_at": datetime.utcnow(),
        }
        return stream_id

    def get_stream(self, stream_id: str) -> dict | None:
        data = self._stream_store.pop(stream_id, None)
        if data is None:
            return None
        if (datetime.utcnow() - data["created_at"]).total_seconds() > 300:
            return None
        return data


session_manager = SessionManager(db=None)  # type: ignore[arg-type]
