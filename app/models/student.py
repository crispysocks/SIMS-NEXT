from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Index
from app.core.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_no = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    age = Column(Integer, nullable=False)
    region = Column(String(50), nullable=False, default="市区", index=True)  # 地区
    native_place = Column(String(100), nullable=True)
    class_id = Column(Integer, nullable=True, index=True)
    enrollment_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_class_id_deleted", "class_id", "is_deleted"),
        Index("idx_region_deleted", "region", "is_deleted"),
    )