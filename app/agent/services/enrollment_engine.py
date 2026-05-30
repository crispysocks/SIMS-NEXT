"""F3: 升学分析引擎——预测上线率和识别临界生（仅初三适用）。"""

from sqlalchemy.orm import Session
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.repositories.student_repo import StudentRepo
from app.agent.repositories.exam_repo import ExamRepo
from app.agent.core.metrics import enrollment_rate, trend_slope
from app.agent.core.config import tier_config


class EnrollmentEngine:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRecordRepo(db)
        self.student_repo = StudentRepo(db)
        self.exam_repo = ExamRepo(db)

    def analyze(
        self,
        class_id: int,
        target_score_line: float | None = None,
    ) -> dict:
        """升学形势分析——基于最近 3 次考试预测上线率。

        Args:
            target_score_line: 目标分数线（百分制），默认 65

        Returns:
            {enrollment_rate, borderline_students, risk_students, summary}
        """
        if target_score_line is None:
            target_score_line = float(tier_config.default_score_line)

        borderline_range = tier_config.borderline_range

        # 获取最近 3 次考试
        exams = self.exam_repo.get_by_class(class_id)
        if not exams:
            return {
                "class_id": class_id,
                "target_score_line": target_score_line,
                "enrollment_rate": 0,
                "borderline_students": [],
                "risk_students": [],
                "summary": "暂无考试数据",
            }

        recent_exams = exams[-3:]
        recent_exam_id = recent_exams[-1]["id"]
        recent_exam_ids = [e["id"] for e in recent_exams]

        # 最近一次考试的各学生总分
        students = self.score_repo.get_student_total_scores(class_id, recent_exam_id)
        if not students:
            return {
                "class_id": class_id,
                "target_score_line": target_score_line,
                "enrollment_rate": 0,
                "borderline_students": [],
                "risk_students": [],
                "summary": "暂无成绩数据",
            }

        exam_total = self.exam_repo.get_by_id(recent_exam_id)
        max_total = exam_total["total_score"] if exam_total else 100

        # 将百分制目标分映射到实际满分
        actual_target = target_score_line / 100 * max_total
        borderline_low = (target_score_line - borderline_range) / 100 * max_total

        # 计算上线率
        total_scores = [s["total_score"] for s in students]
        rate = enrollment_rate(total_scores, actual_target)

        # 识别临界生 (borderline: actual_target - borderline ~ actual_target)
        # 和风险学生 (< borderline_low)
        borderline_students = []
        risk_students = []

        student_info_map = {}
        all_student_nos = [s["student_no"] for s in students]
        for sno in all_student_nos:
            info = self.student_repo.get_by_no(sno)
            if info:
                student_info_map[sno] = info

        for s in students:
            score = s["total_score"]
            info = student_info_map.get(s["student_no"], {})

            # 计算该生在最近几次考试的趋势
            rates = []
            for eid in recent_exam_ids:
                kp_rows = self.score_repo.get_student_kp_scores(s["student_no"], [eid])
                if kp_rows:
                    total_s = sum(r["total_score"] for r in kp_rows)
                    total_m = sum(r["total_max"] for r in kp_rows)
                    rates.append(total_s / total_m if total_m else 0)

            student_trend = "stable"
            if len(rates) >= 2:
                sl = trend_slope(rates)
                if sl > 0.03:
                    student_trend = "rising"
                elif sl < -0.03:
                    student_trend = "falling"

            entry = {
                "student_no": s["student_no"],
                "name": info.get("name", ""),
                "total_score": round(score, 1),
                "rank": s["rank"],
                "trend": student_trend,
            }

            if borderline_low <= score < actual_target:
                borderline_students.append(entry)
            elif score < borderline_low:
                risk_students.append(entry)

        borderline_students.sort(key=lambda x: x["total_score"], reverse=True)
        risk_students.sort(key=lambda x: x["total_score"])

        summary = (
            f"目标分数线 {target_score_line:.0f} 分——"
            f"预估上线率 {rate:.0%}，"
            f"临界生 {len(borderline_students)} 人，"
            f"高风险 {len(risk_students)} 人"
        )

        return {
            "class_id": class_id,
            "target_score_line": target_score_line,
            "enrollment_rate": round(rate, 4),
            "borderline_students": borderline_students,
            "risk_students": risk_students,
            "summary": summary,
        }
