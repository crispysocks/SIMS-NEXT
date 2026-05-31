from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, Index
from app.core.database import Base


class XiyoujiPersona(Base):
    __tablename__ = "xiyouji_persona"
    __table_args__ = {"schema": "sims"}

    id = Column(String(64), primary_key=True)
    chapter = Column(Integer, nullable=False)
    speaker = Column(String(64), nullable=True)
    embedding_text = Column(String(4096), nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class XiyoujiConversation(Base):
    __tablename__ = "xiyouji_conversation"
    __table_args__ = {"schema": "sims", "extend_existing": True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    personality = Column(String(64), nullable=True)
    emotion = Column(String(64), nullable=True)
    tone = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_session_created", "session_id", "created_at"),
    )