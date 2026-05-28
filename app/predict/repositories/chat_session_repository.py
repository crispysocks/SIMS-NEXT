import json
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.predict.models.chat_session import ChatSession


class ChatSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_session(self, student_id: int, minutes: int = 5) -> Optional[ChatSession]:
        """获取指定学生N分钟内的活跃会话"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return self.db.query(ChatSession).filter(
            ChatSession.student_id == student_id,
            ChatSession.last_active_at >= cutoff
        ).order_by(ChatSession.last_active_at.desc()).first()

    def create_session(self, student_id: int) -> ChatSession:
        """创建新会话"""
        session = ChatSession(student_id=student_id, message_count=0, messages='[]')
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def append_message(self, session_id: int, role: str, content: str):
        """追加消息"""
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return

        messages = json.loads(session.messages) if session.messages else []
        messages.append({"role": role, "content": content})
        session.messages = json.dumps(messages, ensure_ascii=False)

        self.db.commit()

    def increment_count(self, session_id: int):
        """message_count += 1"""
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return
        session.message_count += 1
        session.last_active_at = datetime.utcnow()
        self.db.commit()

    def get_session_messages(self, session_id: int) -> List[dict]:
        """获取会话的所有消息"""
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session or not session.messages:
            return []
        return json.loads(session.messages)

    def delete_old_sessions(self, student_id: int, keep_count: int = 1):
        """删除旧会话，保留最新的N个"""
        sessions = self.db.query(ChatSession).filter(
            ChatSession.student_id == student_id
        ).order_by(ChatSession.created_at.desc()).all()

        if len(sessions) <= keep_count:
            return

        for session in sessions[keep_count:]:
            self.db.delete(session)
        self.db.commit()