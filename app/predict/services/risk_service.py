from sqlalchemy.orm import Session
from app.predict.schemas.portrait import RiskWarning
from app.predict.repositories.exam_record_repository import ExamRecordRepository
from app.predict.services.trace_service import traceable


class RiskService:
    def __init__(self, db: Session):
        self.db = db
        self.exam_repo = ExamRecordRepository(db)

    @traceable("RiskService")
    def analyze_risk(self, student_id: int) -> RiskWarning:
        records = self.exam_repo.get_by_student(student_id, limit=30)
        if not records:
            return RiskWarning(risk_level="低", risk_tags=[])

        # Analyze subject-specific risks
        subject_trends = {}
        for r in records:
            if r.subject not in subject_trends:
                subject_trends[r.subject] = []
            subject_trends[r.subject].append(float(r.score))

        risk_tags = []
        for subject, scores in subject_trends.items():
            if len(scores) >= 3:
                trend = scores[-1] - scores[0]
                if trend < -10:
                    risk_tags.append(f"{subject}下滑")
                elif self._is_volatile(scores[-5:]):
                    risk_tags.append(f"{subject}波动")

        # Calculate overall risk level
        if len(risk_tags) >= 3:
            risk_level = "高"
        elif len(risk_tags) >= 1:
            risk_level = "中"
        else:
            risk_level = "低"

        return RiskWarning(risk_level=risk_level, risk_tags=risk_tags)

    def _is_volatile(self, scores: list) -> bool:
        if len(scores) < 3:
            return False
        variance = max(scores) - min(scores)
        return variance > 20