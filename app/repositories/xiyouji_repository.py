from sqlalchemy.orm import Session
from typing import Optional
from app.models.xiyouji import XiyoujiPersona, XiyoujiConversation


class XiyoujiRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_ids(self, ids: list[int]) -> list[XiyoujiPersona]:
        return self.db.query(XiyoujiPersona).filter(XiyoujiPersona.id.in_(ids)).all()

    def get_conversation_history(
        self, session_id: str, limit: int = 20
    ) -> list[XiyoujiConversation]:
        return (
            self.db.query(XiyoujiConversation)
            .filter(XiyoujiConversation.session_id == session_id)
            .order_by(XiyoujiConversation.created_at.asc())
            .limit(limit)
            .all()
        )

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        personality: Optional[str] = None,
        emotion: Optional[str] = None,
        tone: Optional[str] = None,
    ) -> XiyoujiConversation:
        msg = XiyoujiConversation(
            session_id=session_id,
            role=role,
            content=content,
            personality=personality,
            emotion=emotion,
            tone=tone,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg