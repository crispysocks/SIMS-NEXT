from sqlalchemy.orm import Session
from app.predict.schemas.prediction import WhatIfResult
from app.predict.services.prediction_service import PredictionService


class SimulationService:
    SIMULATION_INCREMENTS = [5, 10, 15, 20]

    def __init__(self, db: Session):
        self.db = db
        self.prediction_service = PredictionService(db)

    def simulate(self, student_id: int, student_score: float, subject: str) -> list[WhatIfResult]:
        results = []
        current_prediction = self.prediction_service.predict_student_admission(student_id, student_score)

        if not current_prediction.predictions:
            return results

        # Get key school from first non-empty category
        key_school = None
        for category in ["冲刺", "稳定", "保底"]:
            if current_prediction.predictions.get(category):
                key_school = current_prediction.predictions[category][0]
                break

        if not key_school:
            return results

        for increment in self.SIMULATION_INCREMENTS:
            new_score = student_score + increment
            new_prediction = self.prediction_service.predict_student_admission(student_id, new_score)
            new_key_school = None
            for category in ["冲刺", "稳定", "保底"]:
                if new_prediction.predictions.get(category):
                    new_key_school = new_prediction.predictions[category][0]
                    break

            prob_change = new_key_school.admission_probability - key_school.admission_probability
            prob_change_str = f"+{prob_change}%" if prob_change >= 0 else f"{prob_change}%"

            results.append(WhatIfResult(
                subject=subject,
                score_increase=increment,
                key_high_school_probability_change=prob_change_str,
                ranking_improvement=f"{increment * 2}名"
            ))

        return results