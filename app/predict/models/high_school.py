from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.database import Base


class HighSchool(Base):
    __tablename__ = "high_schools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(100), nullable=False)
    school_level = Column(String(10), nullable=False)  # L1, L2, L3, L4
    region = Column(String(50), nullable=False)
    annual_admission_count = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)