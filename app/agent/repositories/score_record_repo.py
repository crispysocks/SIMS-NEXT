"""成绩记录数据访问层——聚合查询、分组、排名。"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.agent.models.score_record import ScoreRecord
from app.agent.models.question import Question
from app.agent.models.question_kp import QuestionKnowledgePoint
from app.agent.models.knowledge_point import KnowledgePoint
from app.agent.models.exam import Exam
from decimal import Decimal


def _cast(obj):
    """将 Decimal 转为 float，其他类型保持不变。"""
    return float(obj) if isinstance(obj, Decimal) else obj


def _cast_row(row) -> dict:
    """将 SQLAlchemy Row 转为 dict，所有 Decimal 转为 float。"""
    return {k: _cast(v) for k, v in row._asdict().items()}


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
        return [_cast_row(r) for r in rows]

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

        return [_cast_row(r) for r in rows]

    def get_student_total_scores(
        self, class_id: int, exam_id: int
    ) -> list[dict]:
        """获取某班某次考试每个学生的总分和排名。"""
        from app.models.student import Student

        class_student_nos = [
            r[0] for r in
            self.db.query(Student.student_no).filter(Student.class_id == class_id).all()
        ]

        if not class_student_nos:
            return []

        rows = (
            self.db.query(
                ScoreRecord.student_no,
                func.sum(ScoreRecord.score).label("total_score"),
                func.sum(ScoreRecord.max_score).label("total_max"),
            )
            .filter(ScoreRecord.exam_id == exam_id)
            .filter(ScoreRecord.student_no.in_(class_student_nos))
            .group_by(ScoreRecord.student_no)
            .all()
        )

        sorted_rows = sorted(rows, key=lambda r: float(r.total_score), reverse=True)
        results = []
        for rank, r in enumerate(sorted_rows, 1):
            d = r._asdict()
            d["rank"] = rank
            d["total_score"] = float(d["total_score"])
            d["total_max"] = float(d["total_max"])
            d["score_rate"] = d["total_score"] / d["total_max"] if d["total_max"] else 0.0
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

        return [_cast_row(r) for r in rows]

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
        if row and float(row.total_max):
            return float(row.total_score) / float(row.total_max)
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

        common_weak = [_cast_row(r) for r in kp_rows]

        return {
            "avg_score": avg_score,
            "students": [{"student_no": s["student_no"], "total_score": s["total_score"],
                          "rank": s["rank"], "score_rate": s["score_rate"]}
                         for s in top_students],
            "common_weak_kps": common_weak,
        }

    def get_all_class_exam_avgs_by_type(
        self, exam_type: str, semester: str | None = None
    ) -> list[dict]:
        """按考试类型获取年级所有班级的均分排名。

        exam_type 如 '第一次月考'、'期中考试'，各班都有同名考试。
        """
        from app.models.student import Student

        exam_filter = [Exam.exam_type == exam_type]
        if semester:
            exam_filter.append(Exam.semester == semester)

        # 子查询：每个学生在指定考试类型中的总分
        student_totals = (
            self.db.query(
                Exam.class_id,
                ScoreRecord.student_no,
                func.sum(ScoreRecord.score).label("total_score"),
                func.sum(ScoreRecord.max_score).label("total_max"),
            )
            .join(Exam, ScoreRecord.exam_id == Exam.id)
            .filter(and_(*exam_filter))
            .group_by(Exam.class_id, ScoreRecord.student_no)
            .subquery()
        )

        rows = (
            self.db.query(
                student_totals.c.class_id,
                func.count(func.distinct(student_totals.c.student_no)).label("student_count"),
                func.round(func.avg(student_totals.c.total_score), 1).label("avg_score"),
                func.round(func.avg(student_totals.c.total_score / student_totals.c.total_max) * 100, 1).label("avg_rate"),
            )
            .group_by(student_totals.c.class_id)
            .order_by(func.avg(student_totals.c.total_score).desc())
            .all()
        )

        results = []
        for rank, r in enumerate(rows, 1):
            results.append({
                "rank": rank,
                "class_id": int(r.class_id),
                "student_count": int(r.student_count),
                "avg_score": float(r.avg_score),
                "avg_rate": float(r.avg_rate),
            })
        return results

    def get_grade_kp_mastery_by_type(
        self, exam_type: str, kp_ids: list[int] | None = None, semester: str | None = None
    ) -> list[dict]:
        """按考试类型获取年级各知识点在各班的掌握率对比。"""
        exam_filter = [Exam.exam_type == exam_type]
        if semester:
            exam_filter.append(Exam.semester == semester)

        q = (
            self.db.query(
                Exam.class_id,
                QuestionKnowledgePoint.kp_id,
                KnowledgePoint.name.label("kp_name"),
                func.sum(ScoreRecord.score).label("total_score"),
                func.sum(ScoreRecord.max_score).label("total_max"),
            )
            .join(Exam, ScoreRecord.exam_id == Exam.id)
            .join(Question, ScoreRecord.question_id == Question.id)
            .join(QuestionKnowledgePoint, Question.id == QuestionKnowledgePoint.question_id)
            .join(KnowledgePoint, QuestionKnowledgePoint.kp_id == KnowledgePoint.id)
            .filter(and_(*exam_filter))
        )

        if kp_ids:
            q = q.filter(QuestionKnowledgePoint.kp_id.in_(kp_ids))

        rows = q.group_by(Exam.class_id, QuestionKnowledgePoint.kp_id, KnowledgePoint.name).all()

        # 按知识点分组
        from collections import defaultdict
        kp_groups: dict[int, dict] = defaultdict(lambda: {"kp_id": 0, "kp_name": "", "classes": {}})
        for r in rows:
            kp_id = int(r.kp_id)
            kp_groups[kp_id]["kp_id"] = kp_id
            kp_groups[kp_id]["kp_name"] = r.kp_name
            rate = float(r.total_score) / float(r.total_max) if float(r.total_max) else 0
            kp_groups[kp_id]["classes"][int(r.class_id)] = round(rate, 4)

        return sorted(kp_groups.values(), key=lambda x: x["kp_id"])
