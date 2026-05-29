"""成绩记录数据访问层——聚合查询、分组、排名。"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.agent.models.score_record import ScoreRecord
from app.agent.models.question import Question
from app.agent.models.question_kp import QuestionKnowledgePoint
from app.agent.models.knowledge_point import KnowledgePoint
from app.agent.models.exam import Exam


class ScoreRecordRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_class_scores_by_exam(
        self, class_id: int, exam_id: int
    ) -> list[dict]:
        """获取某班某次考试的全部成绩记录（含知识点关联）。"""
        rows = (
            self.db.query(
                ScoreRecord.student_no,
                ScoreRecord.score,
                ScoreRecord.max_score,
                Question.id.label("question_id"),
                Question.question_type,
                QuestionKnowledgePoint.kp_id,
                KnowledgePoint.name.label("kp_name"),
            )
            .join(Question, ScoreRecord.question_id == Question.id)
            .outerjoin(QuestionKnowledgePoint, Question.id == QuestionKnowledgePoint.question_id)
            .outerjoin(
                KnowledgePoint,
                QuestionKnowledgePoint.kp_id == KnowledgePoint.id,
            )
            .filter(ScoreRecord.exam_id == exam_id)
            .all()
        )
        return [r._asdict() for r in rows]

    def get_kp_mastery_by_exams(
        self, class_id: int, exam_ids: list[int], kp_ids: list[int] | None = None
    ) -> list[dict]:
        """按知识点聚合掌握率（跨多次考试）。"""
        q = (
            self.db.query(
                QuestionKnowledgePoint.kp_id,
                KnowledgePoint.name.label("kp_name"),
                KnowledgePoint.level,
                KnowledgePoint.parent_id,
                KnowledgePoint.core_weight,
                func.sum(ScoreRecord.score).label("total_score"),
                func.sum(ScoreRecord.max_score).label("total_max"),
                func.count(func.distinct(ScoreRecord.student_no)).label("student_count"),
            )
            .join(ScoreRecord, ScoreRecord.question_id == QuestionKnowledgePoint.question_id)
            .join(
                KnowledgePoint,
                QuestionKnowledgePoint.kp_id == KnowledgePoint.id,
            )
            .filter(ScoreRecord.exam_id.in_(exam_ids))
        )

        if kp_ids:
            q = q.filter(QuestionKnowledgePoint.kp_id.in_(kp_ids))

        rows = q.group_by(
            QuestionKnowledgePoint.kp_id,
            KnowledgePoint.name,
            KnowledgePoint.level,
            KnowledgePoint.parent_id,
            KnowledgePoint.core_weight,
        ).all()

        return [r._asdict() for r in rows]

    def get_student_total_scores(
        self, class_id: int, exam_id: int
    ) -> list[dict]:
        """获取某班某次考试每个学生的总分和排名。"""
        rows = (
            self.db.query(
                ScoreRecord.student_no,
                func.sum(ScoreRecord.score).label("total_score"),
                func.sum(ScoreRecord.max_score).label("total_max"),
            )
            .filter(ScoreRecord.exam_id == exam_id)
            .group_by(ScoreRecord.student_no)
            .all()
        )

        sorted_rows = sorted(rows, key=lambda r: r.total_score, reverse=True)
        results = []
        for rank, r in enumerate(sorted_rows, 1):
            d = r._asdict()
            d["rank"] = rank
            d["score_rate"] = d["total_score"] / d["total_max"] if d["total_max"] else 0
            results.append(d)
        return results

    def get_student_kp_scores(
        self, student_no: str, exam_ids: list[int], kp_id: int | None = None
    ) -> list[dict]:
        """获取某个学生在指定考试中每个知识点的得分率。"""
        q = (
            self.db.query(
                ScoreRecord.exam_id,
                Exam.name.label("exam_name"),
                Exam.exam_date,
                QuestionKnowledgePoint.kp_id,
                KnowledgePoint.name.label("kp_name"),
                func.sum(ScoreRecord.score).label("total_score"),
                func.sum(ScoreRecord.max_score).label("total_max"),
            )
            .join(Question, ScoreRecord.question_id == Question.id)
            .join(Exam, ScoreRecord.exam_id == Exam.id)
            .join(QuestionKnowledgePoint, Question.id == QuestionKnowledgePoint.question_id)
            .join(KnowledgePoint, QuestionKnowledgePoint.kp_id == KnowledgePoint.id)
            .filter(ScoreRecord.student_no == student_no)
            .filter(ScoreRecord.exam_id.in_(exam_ids))
        )

        if kp_id is not None:
            q = q.filter(QuestionKnowledgePoint.kp_id == kp_id)

        rows = (
            q.group_by(
                ScoreRecord.exam_id,
                Exam.name,
                Exam.exam_date,
                QuestionKnowledgePoint.kp_id,
                KnowledgePoint.name,
            )
            .order_by(Exam.exam_date.asc())
            .all()
        )

        return [r._asdict() for r in rows]

    def get_grade_avg_by_kp(
        self, kp_id: int, exam_ids: list[int]
    ) -> float:
        """获取某知识点在指定考试中的年级平均掌握率。"""
        row = (
            self.db.query(
                func.sum(ScoreRecord.score).label("total_score"),
                func.sum(ScoreRecord.max_score).label("total_max"),
            )
            .join(Question, ScoreRecord.question_id == Question.id)
            .join(QuestionKnowledgePoint, Question.id == QuestionKnowledgePoint.question_id)
            .filter(QuestionKnowledgePoint.kp_id == kp_id)
            .filter(ScoreRecord.exam_id.in_(exam_ids))
            .first()
        )
        if row and row.total_max:
            return row.total_score / row.total_max
        return 0.0

    def get_top_students_summary(
        self, class_id: int, exam_id: int, top_n: int = 10
    ) -> dict:
        """获取前 N 名学生的知识点掌握汇总。"""
        all_students = self.get_student_total_scores(class_id, exam_id)
        top_students = all_students[:top_n]

        if not top_students:
            return {"avg_score": 0, "students": [], "common_weak_kps": []}

        avg_score = sum(s["total_score"] for s in top_students) / len(top_students)

        # 查询前 N 名学生的薄弱知识点（得分率 < 60%）
        student_nos = [s["student_no"] for s in top_students]
        kp_rows = (
            self.db.query(
                QuestionKnowledgePoint.kp_id,
                KnowledgePoint.name.label("kp_name"),
                func.avg(ScoreRecord.score / ScoreRecord.max_score).label("avg_rate"),
            )
            .select_from(ScoreRecord)
            .join(Question, ScoreRecord.question_id == Question.id)
            .join(QuestionKnowledgePoint, Question.id == QuestionKnowledgePoint.question_id)
            .join(KnowledgePoint, QuestionKnowledgePoint.kp_id == KnowledgePoint.id)
            .filter(ScoreRecord.exam_id == exam_id)
            .filter(ScoreRecord.student_no.in_(student_nos))
            .group_by(QuestionKnowledgePoint.kp_id, KnowledgePoint.name)
            .having(func.avg(ScoreRecord.score / ScoreRecord.max_score) < 0.60)
            .order_by(func.avg(ScoreRecord.score / ScoreRecord.max_score).asc())
            .all()
        )

        common_weak = [r._asdict() for r in kp_rows]

        return {
            "avg_score": avg_score,
            "students": [{"student_no": s["student_no"], "total_score": s["total_score"],
                          "rank": s["rank"], "score_rate": s["score_rate"]}
                         for s in top_students],
            "common_weak_kps": common_weak,
        }
