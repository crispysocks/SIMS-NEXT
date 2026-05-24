from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.score_repository import ScoreRepository
from app.repositories.student_repository import StudentRepository
from app.models.score_model import Score
from app.schemas.score_schema import ScoreCreate, ScoreUpdate, ScoreDetail, PaginatedScores


class ScoreService:
    def __init__(self, db: Session):
        self.repo = ScoreRepository(db)
        self.student_repo = StudentRepository(db)

    def create_score(self, data: ScoreCreate) -> ScoreDetail:
        student = self.student_repo.get_by_student_no(data.student_no)
        if not student:
            raise ValueError(f"学生 {data.student_no} 不存在")

        score_obj = Score(
            student_no=data.student_no,
            student_name=student.name,
            exam_name=data.exam_name,
            score=data.score,
        )
        created = self.repo.create(score_obj)
        return ScoreDetail.model_validate(created)

    def get_score(self, score_id: int) -> ScoreDetail:
        score_obj = self.repo.get_by_id(score_id)
        if not score_obj:
            raise ValueError(f"成绩 {score_id} 不存在")
        return ScoreDetail.model_validate(score_obj)

    def list_scores(
        self,
        student_no: Optional[str] = None,
        exam_name: Optional[str] = None,
        student_name: Optional[str] = None
    ) -> PaginatedScores:
        scores = self.repo.list(student_no, exam_name, student_name)
        return PaginatedScores(
            items=[ScoreDetail.model_validate(s) for s in scores],
            total=len(scores)
        )

    def update_score(self, score_id: int, data: ScoreUpdate) -> ScoreDetail:
        score_obj = self.repo.get_by_id(score_id)
        if not score_obj:
            raise ValueError(f"成绩 {score_id} 不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(score_obj, key, value)

        updated = self.repo.update(score_obj)
        return ScoreDetail.model_validate(updated)

    def delete_score(self, score_id: int) -> None:
        score_obj = self.repo.get_by_id(score_id)
        if not score_obj:
            raise ValueError(f"成绩 {score_id} 不存在")

        self.repo.soft_delete(score_obj)