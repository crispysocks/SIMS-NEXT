from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.database import Base


class ScoreRankLine(Base):
    __tablename__ = "score_rank_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey("high_schools.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)