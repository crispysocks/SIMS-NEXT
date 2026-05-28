from sqlalchemy.orm import Session
from app.predict.models.student_portrait import StudentPortrait

# Import Student to ensure the FK target is resolved
from app.models.student import Student


class PortraitRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_student(self, student_id: int) -> StudentPortrait | None:
        return self.db.query(StudentPortrait).filter(
            StudentPortrait.student_id == student_id,
            StudentPortrait.is_deleted == False
        ).first()

    def upsert(self, student_id: int, data: dict) -> StudentPortrait:
        portrait = self.get_by_student(student_id)
        if portrait:
            for key, value in data.items():
                setattr(portrait, key, value)
        else:
            portrait = StudentPortrait(student_id=student_id, **data)
            self.db.add(portrait)
        self.db.commit()
        self.db.refresh(portrait)
        return portrait