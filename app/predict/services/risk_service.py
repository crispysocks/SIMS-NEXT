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
        high_volatility_count = 0

        for subject, scores in subject_trends.items():
            if len(scores) >= 3:
                trend = scores[-1] - scores[0]
                if trend < -10:
                    risk_tags.append(f"{subject}下滑")

                # Check volatility - only high volatility (variance > 30) counts as risk
                if len(scores) >= 5:
                    variance = max(scores[-5:]) - min(scores[-5:])
                    if variance > 30:
                        risk_tags.append(f"{subject}波动大")
                        high_volatility_count += 1

        # Calculate overall risk level - reduced volatility weight
        # Only high volatility (variance > 30) and subject decline count as real risks
        risk_count = len(risk_tags)
        if risk_count >= 3:
            risk_level = "高"
        elif risk_count >= 1 or high_volatility_count >= 2:
            risk_level = "中"
        else:
            risk_level = "低"

        return RiskWarning(risk_level=risk_level, risk_tags=risk_tags)

    def _is_volatile(self, scores: list) -> bool:
        if len(scores) < 3:
            return False
        variance = max(scores) - min(scores)
        return variance > 20