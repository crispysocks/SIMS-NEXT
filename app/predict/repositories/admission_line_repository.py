from sqlalchemy.orm import Session
from app.predict.models.admission_line import AdmissionScoreLine


class AdmissionLineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_school(self, school_id: int, limit_years: int = 5) -> list[AdmissionScoreLine]:
        return self.db.query(AdmissionScoreLine).filter(
            AdmissionScoreLine.school_id == school_id,
            AdmissionScoreLine.is_deleted == False
        ).order_by(AdmissionScoreLine.year.desc()).limit(limit_years).all()

    def get_latest_by_school(self, school_id: int) -> AdmissionScoreLine | None:
        return self.db.query(AdmissionScoreLine).filter(
            AdmissionScoreLine.school_id == school_id,
            AdmissionScoreLine.is_deleted == False
        ).order_by(AdmissionScoreLine.year.desc()).first()

    def get_by_school_and_year(self, school_id: int, year: int) -> AdmissionScoreLine | None:
        return self.db.query(AdmissionScoreLine).filter(
            AdmissionScoreLine.school_id == school_id,
            AdmissionScoreLine.year == year,
            AdmissionScoreLine.is_deleted == False
        ).first()

    def create(self, data: dict) -> AdmissionScoreLine:
        line = AdmissionScoreLine(**data)
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line