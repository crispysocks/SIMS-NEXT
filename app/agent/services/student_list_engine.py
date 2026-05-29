"""F5: 培优补差名单引擎——识别有潜力的培优生和需要帮扶的补差生。"""

from sqlalchemy.orm import Session
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.repositories.student_repo import StudentRepo
from app.agent.core.metrics import kp_mastery_rate


class StudentListEngine:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRecordRepo(db)
        self.student_repo = StudentRepo(db)

    def get_advanced(self, class_id: int, exam_id: int) -> dict:
        """培优名单——总分排名前 30% 但存在薄弱知识点的学生。

        这类学生基础好但有个别短板，有较大提分空间。
        """
        students = self.score_repo.get_student_total_scores(class_id, exam_id)
        if not students:
            return {"class_id": class_id, "exam_id": exam_id, "students": [], "common_weak_kps": []}

        n = len(students)
        top30_count = max(1, int(n * 0.30))
        top30 = students[:top30_count]

        # 检查每个前 30% 学生的薄弱知识点
        advanced = []
        for s in top30:
            kp_scores = self.score_repo.get_student_kp_scores(
                s["student_no"], [exam_id]
            )
            weak_kps = []
            for ks in kp_scores:
                rate = ks["total_score"] / ks["total_max"] if ks["total_max"] else 0
                if rate < 0.60:
                    weak_kps.append({
                        "kp_id": ks["kp_id"],
                        "kp_name": ks["kp_name"],
                        "score_rate": round(rate, 4),
                    })

            if weak_kps:
                student_info = self.student_repo.get_by_no(s["student_no"])
                advanced.append({
                    "student_no": s["student_no"],
                    "name": student_info["name"] if student_info else "",
                    "total_score": s["total_score"],
                    "rank": s["rank"],
                    "weak_kps": weak_kps,
                })

        # 共同薄弱点
        common_weak = self._find_common_weak_kps(
            [a["student_no"] for a in advanced], exam_id
        )

        return {
            "class_id": class_id,
            "exam_id": exam_id,
            "students": advanced,
            "common_weak_kps": common_weak,
        }

    def get_remedial(self, class_id: int, exam_id: int) -> dict:
        """补差名单——总分排名后 30% 且多个核心知识点薄弱的学生。

        这类学生基础较差，需要系统性帮扶。
        """
        students = self.score_repo.get_student_total_scores(class_id, exam_id)
        if not students:
            return {"class_id": class_id, "exam_id": exam_id, "students": [], "common_weak_kps": []}

        n = len(students)
        bottom30_count = max(1, int(n * 0.30))
        bottom30 = students[-bottom30_count:]

        remedial = []
        for s in bottom30:
            kp_scores = self.score_repo.get_student_kp_scores(
                s["student_no"], [exam_id]
            )
            weak_kps = []
            for ks in kp_scores:
                rate = ks["total_score"] / ks["total_max"] if ks["total_max"] else 0
                if rate < 0.50:
                    weak_kps.append({
                        "kp_id": ks["kp_id"],
                        "kp_name": ks["kp_name"],
                        "score_rate": round(rate, 4),
                    })

            if len(weak_kps) >= 3:  # 多个薄弱点才算补差
                student_info = self.student_repo.get_by_no(s["student_no"])
                remedial.append({
                    "student_no": s["student_no"],
                    "name": student_info["name"] if student_info else "",
                    "total_score": s["total_score"],
                    "rank": s["rank"],
                    "weak_kps": weak_kps,
                })

        common_weak = self._find_common_weak_kps(
            [r["student_no"] for r in remedial], exam_id
        )

        return {
            "class_id": class_id,
            "exam_id": exam_id,
            "students": remedial,
            "common_weak_kps": common_weak,
        }

    def _find_common_weak_kps(
        self, student_nos: list[str], exam_id: int
    ) -> list[dict]:
        """找出名单中学生的共同薄弱知识点。"""
        if not student_nos:
            return []

        from collections import Counter
        weak_counter: Counter = Counter()

        for sno in student_nos:
            kp_scores = self.score_repo.get_student_kp_scores(sno, [exam_id])
            weak_for_student = set()
            for ks in kp_scores:
                rate = ks["total_score"] / ks["total_max"] if ks["total_max"] else 0
                if rate < 0.60:
                    weak_for_student.add((ks["kp_id"], ks["kp_name"]))
            weak_counter.update(weak_for_student)

        threshold = max(2, len(student_nos) * 0.4)
        return [
            {"kp_id": kp_id, "name": name, "count": count}
            for (kp_id, name), count in weak_counter.most_common(10)
            if count >= threshold
        ]
