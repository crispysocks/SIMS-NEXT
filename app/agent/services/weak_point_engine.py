"""F1: 薄弱知识点分析引擎——基于聚合数据识别薄弱知识点。"""

from sqlalchemy.orm import Session
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.repositories.knowledge_point_repo import KnowledgePointRepo
from app.agent.core.metrics import kp_mastery_rate, class_deviation
from app.agent.core.config import tier_config


class WeakPointEngine:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRecordRepo(db)
        self.kp_repo = KnowledgePointRepo(db)

    def analyze(
        self,
        class_id: int,
        exam_ids: list[int],
        kp_ids: list[int] | None = None,
    ) -> dict:
        """分析薄弱知识点。

        按知识点聚合掌握率，计算班级得分率和年级偏差，
        标注得分率低于阈值的薄弱点。

        Returns:
            {knowledge_points: [{kp_id, name, level, parent_id,
              mastery_rate, class_avg_score, grade_avg_score,
              deviation, discrimination, is_weak}], summary}
        """
        # 1. 从成绩记录聚合知识点掌握数据
        kp_data = self.score_repo.get_kp_mastery_by_exams(class_id, exam_ids, kp_ids)

        if not kp_data:
            return {
                "class_id": class_id,
                "exam_ids": exam_ids,
                "knowledge_points": [],
                "summary": "暂无数据",
            }

        threshold = tier_config.weak_point_threshold
        results = []
        weak_count = 0

        for row in kp_data:
            mastery = kp_mastery_rate(
                [row["total_score"]], [row["total_max"]]
            )

            # 年级平均（简化：直接用班级值，因为 Mock 数据目前没有跨班查询）
            # 后续接入真实数据后可替换为 get_grade_avg_by_kp
            grade_mastery = self.score_repo.get_grade_avg_by_kp(
                row["kp_id"], exam_ids
            )
            deviation = class_deviation(mastery, grade_mastery)

            is_weak = mastery < threshold

            if is_weak:
                weak_count += 1

            results.append({
                "kp_id": row["kp_id"],
                "name": row["kp_name"],
                "level": row["level"],
                "parent_id": row["parent_id"],
                "mastery_rate": round(mastery, 4),
                "class_avg_score": round(row["total_score"] / row["student_count"], 2)
                if row["student_count"] else 0,
                "grade_avg_score": round(grade_mastery, 4),
                "deviation": round(deviation, 4),
                "discrimination": 0.0,  # 后续可通过 discrimination_index 计算
                "core_weight": row.get("core_weight", 1.0),
                "is_weak": is_weak,
            })

        # 按掌握率排序（最低的在前）
        results.sort(key=lambda x: x["mastery_rate"])

        weak_kps = [r for r in results if r["is_weak"]]
        top_weak = weak_kps[:3]
        top_weak_str = "、".join(
            f"{kp['name']}({kp['mastery_rate']:.0%})" for kp in top_weak
        ) if top_weak else "无"

        summary = (
            f"共分析 {len(results)} 个知识点，{weak_count} 个薄弱"
            f"（阈值 {threshold:.0%}）。"
            f"最薄弱: {top_weak_str}"
        )

        return {
            "class_id": class_id,
            "exam_ids": exam_ids,
            "knowledge_points": results,
            "summary": summary,
        }
