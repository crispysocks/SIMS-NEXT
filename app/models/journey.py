from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, Boolean, JSON, DateTime, Index
from app.core.database import Base


class JourneyConversation(Base):
    __tablename__ = "xiyouji_conversation"
    __table_args__ = (
        Index("idx_jconv_session_created", "session_id", "created_at"),
        {"schema": "sims", "extend_existing": True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    personality = Column(String(64), nullable=True)
    emotion = Column(String(64), nullable=True)
    tone = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class JourneyState(Base):
    __tablename__ = "xiyouji_journey"
    __table_args__ = (
        Index("idx_jstate_session_active", "session_id", "is_active"),
        {"schema": "sims", "extend_existing": True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    user_role = Column(String(64), default="五徒弟")
    current_stage = Column(String(32))
    progress = Column(Integer, default=0)
    karma = Column(Integer, default=0)
    companions = Column(JSON)
    chapter = Column(Integer, default=1)
    level_id = Column(Integer, default=1)
    stage_data = Column(JSON)
    knowledge_cards = Column(JSON, default=list)
    achievements = Column(JSON, default=list)
    cleared_chapters = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JourneyPersona(Base):
    __tablename__ = "xiyouji_persona"
    __table_args__ = {"schema": "sims"}

    id = Column(String(64), primary_key=True)
    chapter = Column(Integer, nullable=False)
    speaker = Column(String(64), nullable=True)
    embedding_text = Column(String(4096), nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
