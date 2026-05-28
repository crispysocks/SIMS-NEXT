from sqlalchemy.orm import Session
from app.predict.models.high_school import HighSchool


class HighSchoolRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, school_id: int) -> HighSchool | None:
        return self.db.query(HighSchool).filter(
            HighSchool.id == school_id,
            HighSchool.is_deleted == False
        ).first()

    def get_by_level(self, level: str) -> list[HighSchool]:
        return self.db.query(HighSchool).filter(
            HighSchool.school_level == level,
            HighSchool.is_deleted == False
        ).all()

    def get_all(self) -> list[HighSchool]:
        return self.db.query(HighSchool).filter(
            HighSchool.is_deleted == False
        ).all()

    def create(self, data: dict) -> HighSchool:
        school = HighSchool(**data)
        self.db.add(school)
        self.db.commit()
        self.db.refresh(school)
        return school