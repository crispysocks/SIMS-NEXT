"""学科表——如"初中数学"。"""

from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Subject(Base):
    __tablename__ = "agent_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    grade_level = Column(String(20), nullable=False)  # "初中" / "高中"
    description = Column(String(200), nullable=True)
