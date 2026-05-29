"""题目质量分析——区分度 + 实际难度系数计算。"""

from sqlalchemy.orm import Session
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.core.metrics import discrimination_index, difficulty_coefficient
from app.agent.core.config import tier_config


class QuestionQualityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ScoreRecordRepo(db)

    def analyze(
        self, exam_id: int, question_ids: list[int] | None = None
    ) -> dict:
        """分析某次考试题目的区分度和难度系数。

        Returns:
            {questions: [{question_id, title, difficulty, discrimination, quality_label}]}
        """
        # 获取所有题目
        from app.agent.models.question import Question

        q = self.db.query(Question).filter(Question.exam_id == exam_id)
        if question_ids:
            q = q.filter(Question.id.in_(question_ids))
        questions = q.order_by(Question.sort_order.asc()).all()

        results = []
        low_quality_count = 0

        for question in questions:
            # 获取该题目的所有得分记录
            from app.agent.models.score_record import ScoreRecord

            records = (
                self.db.query(ScoreRecord.score, ScoreRecord.max_score)
                .filter(ScoreRecord.question_id == question.id)
                .all()
            )

            scores = [r.score for r in records]
            max_scores = [r.max_score for r in records]

            disc = discrimination_index(scores, max_scores) if scores else 0
            diff = difficulty_coefficient(scores, max_scores) if scores else 0

            threshold = tier_config.low_discrimination_threshold
            if disc >= 0.4:
                quality_label = "优秀"
            elif disc >= threshold:
                quality_label = "一般"
            else:
                quality_label = "低质量"
                low_quality_count += 1

            results.append({
                "question_id": question.id,
                "title": question.title or f"题{question.sort_order}",
                "difficulty": round(diff, 3),
                "discrimination": round(disc, 3),
                "quality_label": quality_label,
            })

        return {
            "exam_id": exam_id,
            "questions": results,
            "low_quality_count": low_quality_count,
        }
