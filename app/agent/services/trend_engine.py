"""F2: 趋势分析引擎——班级均分走势 + 知识点掌握率变化趋势。"""

from sqlalchemy.orm import Session
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.repositories.exam_repo import ExamRepo
from app.agent.core.metrics import trend_slope
from app.agent.core.config import tier_config


class TrendEngine:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRecordRepo(db)
        self.exam_repo = ExamRepo(db)

    def analyze(self, class_id: int, exam_ids: list[int]) -> dict:
        """分析班级在多次考试中的趋势。

        Returns:
            {exam_avgs, slope, direction, weak_kp_trends, summary}
        """
        exams = self.exam_repo.get_by_ids(exam_ids)
        if len(exams) < 2:
            return {
                "class_id": class_id,
                "exam_ids": exam_ids,
                "exam_avgs": [],
                "slope": 0,
                "direction": "数据不足（需要至少 2 次考试）",
                "weak_kp_trends": [],
                "summary": "需要至少 2 次考试才能做趋势分析",
            }

        # 每次考试的班级均分
        exam_avgs = []
        for exam_id in exam_ids:
            students = self.score_repo.get_student_total_scores(class_id, exam_id)
            if students:
                avg = sum(s["total_score"] for s in students) / len(students)
                exam_avgs.append(round(avg, 1))
            else:
                exam_avgs.append(0.0)

        slope = trend_slope(exam_avgs)

        # 判断趋势方向
        decline_threshold = tier_config.decline_threshold
        improve_threshold = tier_config.improve_threshold

        if slope > improve_threshold:
            direction = "上升"
        elif slope < decline_threshold:
            direction = "下降"
        elif abs(slope) < 1.0:
            direction = "持平"
        else:
            direction = "波动"

        # 薄弱知识点趋势（从第一次到最近一次）
        first_exam = exam_ids[0]
        last_exam = exam_ids[-1]

        weak_kp_trends = []
        first_data = self.score_repo.get_kp_mastery_by_exams(class_id, [first_exam])
        last_data = self.score_repo.get_kp_mastery_by_exams(class_id, [last_exam])

        first_map = {}
        for row in first_data:
            rate = row["total_score"] / row["total_max"] if row["total_max"] else 0
            first_map[row["kp_id"]] = rate

        for row in last_data:
            rate = row["total_score"] / row["total_max"] if row["total_max"] else 0
            kp_id = row["kp_id"]
            if kp_id in first_map and rate < 0.60:
                delta = rate - first_map[kp_id]
                weak_kp_trends.append({
                    "kp_id": kp_id,
                    "kp_name": row["kp_name"],
                    "first_rate": round(first_map[kp_id], 4),
                    "last_rate": round(rate, 4),
                    "delta": round(delta, 4),
                })

        weak_kp_trends.sort(key=lambda x: x["delta"])

        exam_names = [e["name"] for e in exams]
        summary = (
            f"基于 {len(exams)} 次考试趋势分析："
            f"班级均分从 {exam_avgs[0]} 到 {exam_avgs[-1]}，"
            f"趋势 {direction}（斜率 {slope:.2f}）"
        )

        return {
            "class_id": class_id,
            "exam_ids": exam_ids,
            "exam_names": exam_names,
            "exam_avgs": exam_avgs,
            "slope": round(slope, 4),
            "direction": direction,
            "weak_kp_trends": weak_kp_trends,
            "summary": summary,
        }
