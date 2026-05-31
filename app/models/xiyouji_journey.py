from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, JSON, DateTime, Index
from app.core.database import Base


class XiyoujiJourney(Base):
    __tablename__ = "xiyouji_journey"
    __table_args__ = {"schema": "sims", "extend_existing": True}

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

    __table_args__ = (
        Index("idx_journey_session", "session_id", "is_active"),
    )