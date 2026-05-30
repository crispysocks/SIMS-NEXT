"""F4: 分层教学引擎——按总分排名将学生分为 A/B/C/D 四层。"""

from sqlalchemy.orm import Session
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.core.metrics import tier_thresholds
from app.agent.core.config import tier_config


class TierEngine:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ScoreRecordRepo(db)

    def analyze(self, class_id: int, exam_id: int) -> dict:
        """按单次考试总分对学生进行四层分层。

        Returns:
            {tiers: {A/B/C/D: {label, students, avg_score, headcount, rank_range}}}
        """
        students = self.repo.get_student_total_scores(class_id, exam_id)

        if not students:
            return {
                "class_id": class_id,
                "exam_id": exam_id,
                "tiers": {},
                "summary": "暂无成绩数据",
            }

        scores = [s["total_score"] for s in students]
        thresholds = tier_thresholds(scores)
        tiers_def = tier_config.get_all_tiers()
        protection = tier_config.get_protection_rules()

        tiers = {
            "A": {"label": tiers_def["A"]["label"], "students": [], "avg_score": 0, "headcount": 0, "rank_range": ""},
            "B": {"label": tiers_def["B"]["label"], "students": [], "avg_score": 0, "headcount": 0, "rank_range": ""},
            "C": {"label": tiers_def["C"]["label"], "students": [], "avg_score": 0, "headcount": 0, "rank_range": ""},
            "D": {"label": tiers_def["D"]["label"], "students": [], "avg_score": 0, "headcount": 0, "rank_range": ""},
        }

        n = len(students)
        for student in students:
            score = student["total_score"]
            if score >= thresholds["A_min"]:
                tiers["A"]["students"].append(student)
            elif score >= thresholds["B_min"]:
                tiers["B"]["students"].append(student)
            elif score >= thresholds["C_min"]:
                tiers["C"]["students"].append(student)
            else:
                tiers["D"]["students"].append(student)

        # 保护规则：每层最少人数
        min_size = protection.get("min_tier_size", 3)
        all_tier_keys = list(tiers.keys())

        for tier_key in tiers:
            tier = tiers[tier_key]
            tier["headcount"] = len(tier["students"])
            if tier["headcount"] < min_size and tier["headcount"] > 0:
                # 从相邻层借调学生
                current_idx = all_tier_keys.index(tier_key)
                if current_idx > 0:
                    prev_key = all_tier_keys[current_idx - 1]
                    if len(tiers[prev_key]["students"]) > min_size:
                        move_count = min_size - tier["headcount"]
                        moved = tiers[prev_key]["students"][-move_count:]
                        tier["students"] = moved + tier["students"]
                        tiers[prev_key]["students"] = tiers[prev_key]["students"][:-move_count]

            if tier["students"]:
                tier_avg = sum(s["total_score"] for s in tier["students"]) / len(tier["students"])
                tier["avg_score"] = round(tier_avg, 1)

            tier["headcount"] = len(tier["students"])

        # 更新排名范围
        for tier_key in tiers:
            tier = tiers[tier_key]
            if tier["students"]:
                ranks = [s["rank"] for s in tier["students"]]
                tier["rank_range"] = f"{min(ranks)}-{max(ranks)}"

        # 生成摘要
        tier_summaries = []
        for key in ["A", "B", "C", "D"]:
            t = tiers[key]
            tier_summaries.append(
                f"{t['label']}{t['headcount']}人(均分{t['avg_score']:.1f})"
            )
        summary = "分层结果: " + "、".join(tier_summaries)

        return {
            "class_id": class_id,
            "exam_id": exam_id,
            "tiers": tiers,
            "summary": summary,
        }
