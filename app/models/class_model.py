from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Index
from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_no = Column(String(50), unique=True, nullable=False, index=True)
    class_name = Column(String(100), nullable=False)
    head_teacher_no = Column(String(20), unique=True, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_class_no_deleted", "class_no", "is_deleted"),
        Index("idx_head_teacher_no_deleted", "head_teacher_no", "is_deleted"),
    )