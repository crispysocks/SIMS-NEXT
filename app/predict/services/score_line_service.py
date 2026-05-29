from sqlalchemy.orm import Session
from app.predict.repositories.admission_line_repository import AdmissionLineRepository
from app.predict.repositories.high_school_repository import HighSchoolRepository
from app.predict.schemas.admission_line import ScoreLinePrediction


class ScoreLineService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AdmissionLineRepository(db)
        self.school_repo = HighSchoolRepository(db)

    def predict_score_line(self, school_id: int, target_year: int) -> ScoreLinePrediction | None:
        history_lines = self.repo.get_by_school(school_id, limit_years=10)
        if not history_lines:
            return None

        school = self.school_repo.get_by_id(school_id)
        if not school:
            return None

        years = [line.year for line in history_lines]
        scores = [float(line.admission_score) for line in history_lines]

        n = len(years)
        if n < 2:
            last_year_score = scores[0]
            predicted_score = last_year_score
        else:
            # Simple linear regression: y = a*x + b
            x_mean = sum(years) / n
            y_mean = sum(scores) / n

            numerator = sum((years[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
            denominator = sum((years[i] - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                last_year_score = scores[0]
                predicted_score = last_year_score
            else:
                slope = numerator / denominator
                intercept = y_mean - slope * x_mean
                predicted_score = slope * target_year + intercept
                last_year_score = scores[0]

        fluctuation = predicted_score - last_year_score

        return ScoreLinePrediction(
            school_name=school.school_name,
            last_year_score=last_year_score,
            predicted_score=round(predicted_score, 2),
            fluctuation=f"+{round(fluctuation, 2)}" if fluctuation >= 0 else str(round(fluctuation, 2))
        )