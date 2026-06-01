from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.core.database import Base


class ScoreRankLine(Base):
    __tablename__ = "score_rank_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)
    score_min = Column(Integer, nullable=False)
    score_max = Column(Integer, nullable=False)
    rank_min = Column(Integer, nullable=False)
    rank_max = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, nullable=True)