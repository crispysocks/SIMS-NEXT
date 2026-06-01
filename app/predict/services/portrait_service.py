from sqlalchemy.orm import Session
from app.predict.schemas.portrait import StudentPortraitDetail
from app.predict.repositories.portrait_repository import PortraitRepository
from app.predict.repositories.exam_record_repository import ExamRecordRepository
from app.predict.services.trace_service import traceable


class PortraitService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PortraitRepository(db)
        self.exam_repo = ExamRecordRepository(db)

    @traceable("PortraitService")
    def analyze_student(self, student_id: int) -> StudentPortraitDetail | None:
        records = self.exam_repo.get_by_student(student_id, limit=50)
        if not records:
            return None

        # Analyze learning type based on score trends
        learning_type = self._analyze_learning_type(records)
        science_ability = self._analyze_subject_ability(records, ["数学", "物理", "化学"])
        english_ability = self._analyze_subject_ability(records, ["英语", "语文"])
        improvement_potential = self._calculate_improvement_potential(records)

        data = {
            "learning_type": learning_type,
            "science_ability": science_ability,
            "english_ability": english_ability,
            "improvement_potential": improvement_potential,
        }

        portrait = self.repo.upsert(student_id, data)
        return StudentPortraitDetail.model_validate(portrait)

    def _analyze_learning_type(self, records) -> str:
        scores_by_exam = {}
        for r in records:
            if r.exam_name not in scores_by_exam:
                scores_by_exam[r.exam_name] = []
            scores_by_exam[r.exam_name].append(float(r.score))

        exam_averages = [sum(s) / len(s) for s in scores_by_exam.values()]
        if len(exam_averages) < 2:
            return "稳定提升型"

        trends = [exam_averages[i + 1] - exam_averages[i] for i in range(len(exam_averages) - 1)]
        avg_trend = sum(trends) / len(trends) if trends else 0

        if avg_trend > 2:
            return "稳定提升型"
        elif avg_trend < -2:
            return "退步型"
        else:
            return "波动型"

    def _analyze_subject_ability(self, records, subjects: list[str]) -> str:
        subject_scores = {s: [] for s in subjects}
        for r in records:
            if r.subject in subjects:
                subject_scores[r.subject].append(float(r.score))

        avg_scores = []
        for s, scores in subject_scores.items():
            if scores:
                avg_scores.append(sum(scores) / len(scores))

        if not avg_scores:
            return "中"
        overall_avg = sum(avg_scores) / len(avg_scores)

        if overall_avg >= 85:
            return "强"
        elif overall_avg >= 70:
            return "中"
        else:
            return "弱"

    def _calculate_improvement_potential(self, records) -> str:
        scores = [float(r.score) for r in records if r.subject in ["数学", "英语"]]
        if len(scores) < 3:
            return "中"
        variance = self._calculate_variance(scores[-5:])
        if variance > 100:
            return "高"
        elif variance > 50:
            return "中"
        else:
            return "低"

    def _calculate_variance(self, values: list) -> float:
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)