"""知识点跨考试对比引擎——追踪单个学生或班级的知识点变化。"""

from sqlalchemy.orm import Session
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.repositories.exam_repo import ExamRepo
from app.agent.core.metrics import trend_slope


class KPComparisonEngine:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRecordRepo(db)
        self.exam_repo = ExamRepo(db)

    def get_student_trend(
        self,
        student_no: str,
        exam_ids: list[int],
        kp_id: int | None = None,
    ) -> dict:
        """获取单个学生在历次考试中的知识点得分率变化。

        Returns:
            {student_no, kp_id, trend, slope, data_points: [{exam_id, exam_name, score_rate}]}
        """
        rows = self.score_repo.get_student_kp_scores(student_no, exam_ids, kp_id)
        exams = {e["id"]: e for e in self.exam_repo.get_by_ids(exam_ids)}

        # 按考试聚合（如果 kp_id 为 None 则汇总所有知识点）
        exam_rates = {}
        for row in rows:
            eid = row["exam_id"]
            if eid not in exam_rates:
                exam_rates[eid] = {"total_score": 0, "total_max": 0}
            exam_rates[eid]["total_score"] += row["total_score"]
            exam_rates[eid]["total_max"] += row["total_max"]

        data_points = []
        for eid in sorted(exam_rates.keys()):
            d = exam_rates[eid]
            rate = d["total_score"] / d["total_max"] if d["total_max"] else 0
            data_points.append({
                "exam_id": eid,
                "exam_name": exams.get(eid, {}).get("name", ""),
                "score_rate": round(rate, 4),
            })

        rates = [p["score_rate"] for p in data_points]
        slope = trend_slope(rates) if len(rates) >= 2 else 0

        if slope > 0.03:
            trend = "rising"
        elif slope < -0.03:
            trend = "falling"
        elif len(rates) >= 3 and max(rates) - min(rates) > 0.15:
            trend = "volatile"
        else:
            trend = "stable"

        return {
            "student_no": student_no,
            "kp_id": kp_id,
            "trend": trend,
            "slope": round(slope, 4),
            "data_points": data_points,
        }

    def compare_kps(
        self,
        class_id: int,
        kp_ids: list[int],
        exam_ids: list[int],
    ) -> dict:
        """对比多个知识点在多次考试中的掌握率变化。

        Returns:
            {comparison: [{kp_id, kp_name, exam_rates: [{exam_id, rate}]}]}
        """
        comparison = []
        for kp_id in kp_ids:
            exam_rates = []
            for exam_id in exam_ids:
                data = self.score_repo.get_kp_mastery_by_exams(
                    class_id, [exam_id], [kp_id]
                )
                if data:
                    d = data[0]
                    rate = d["total_score"] / d["total_max"] if d["total_max"] else 0
                    exam_rates.append({"exam_id": exam_id, "rate": round(rate, 4)})

            kp_info = data[0] if data else {}
            comparison.append({
                "kp_id": kp_id,
                "kp_name": kp_info.get("kp_name", ""),
                "exam_rates": exam_rates,
            })

        return {"comparison": comparison, "exam_ids": exam_ids}
