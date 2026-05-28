import statistics
from sqlalchemy.orm import Session
from app.predict.schemas.prediction import StudentPrediction, PredictionItem
from app.predict.services.score_line_service import ScoreLineService
from app.predict.repositories.high_school_repository import HighSchoolRepository
from app.predict.repositories.admission_line_repository import AdmissionLineRepository
from app.predict.repositories.exam_record_repository import ExamRecordRepository
from app.predict.repositories.score_rank_line_repository import ScoreRankLineRepository
from app.models.student import Student
from app.predict.services.trace_service import traceable


class PredictionService:
    TYPE_LIMITS = {
        "冲刺": 2,
        "稳定": 3,
        "保底": 2
    }

    # 三档概率阈值
    PROB_THRESHOLD = {
        "冲刺": 40,   # < 40% → 冲刺
        "稳定": 75,   # 40% ≤ prob < 75% → 稳定
        "保底": 100   # ≥ 75% → 保底
    }

    def __init__(self, db: Session):
        self.db = db
        self.score_line_service = ScoreLineService(db)

    @traceable("PredictionService")
    def predict_student_admission(self, student_id: int, student_score: float) -> StudentPrediction:
        exam_repo = ExamRecordRepository(self.db)
        school_repo = HighSchoolRepository(self.db)
        line_repo = AdmissionLineRepository(self.db)
        rank_line_repo = ScoreRankLineRepository(self.db)

        # 1. 获取学生信息和历史成绩
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return self._empty_prediction(student_id, student_score)

        latest_records = exam_repo.get_latest_by_student(student_id)
        if not latest_records:
            return self._empty_prediction(student_id, student_score)

        current_ranking = latest_records[0].ranking if latest_records else 1

        # 2. 计算学生能力值
        ability_info = self._calculate_student_ability(latest_records)
        avg_score = ability_info["avg_score"]
        ranking_stability = ability_info["ranking_stability"]
        ranking_trend = ability_info["ranking_trend"]

        # 3. 将能力分转换为排名
        year = 2026
        region = student.region or "城区"
        # 用用户传入的当前总分查一分一段表获取预测排名
        student_predicted_rank = rank_line_repo.score_to_rank(student_score, region, year)

        schools = school_repo.get_all()

        school_data = []
        for school in schools:
            line_pred = self.score_line_service.predict_score_line(school.id, year)
            latest_line = line_repo.get_latest_by_school(school.id)
            if line_pred and latest_line:
                school_data.append({
                    "school_id": school.id,
                    "school_name": school.school_name,
                    "predicted_score": line_pred.predicted_score,
                    "admission_rank": latest_line.admission_rank,
                    "enrollment_count": latest_line.student_count,
                })

        if not school_data:
            return self._empty_prediction(student_id, student_score)

        # 4. 计算每所学校的录取概率
        for sc in school_data:
            prob = self._calculate_admission_probability(
                student_score=student_score,
                student_predicted_rank=student_predicted_rank,
                ranking_stability=ranking_stability,
                admission_rank=sc["admission_rank"],
                enrollment_count=sc["enrollment_count"],
                target_score=sc["predicted_score"],
            )
            sc["admission_probability"] = prob

        # 5. 三档分类（概率优先）
        # 问题：学生分数75-85，学校分数395-540，差值必然<-30
        # 解决：主要依赖概率分组，分数差作为辅助判断
        for sc in school_data:
            prob = sc["admission_probability"]

            if prob < self.PROB_THRESHOLD["冲刺"]:
                ad_type = "冲刺"
            elif prob < self.PROB_THRESHOLD["稳定"]:
                ad_type = "稳定"
            else:
                ad_type = "保底"

            sc["admission_type"] = ad_type

        # 6. 分组和排序
        grouped = {"冲刺": [], "稳定": [], "保底": [], "超出分数线": [], "低于分数线": []}

        for sc in school_data:
            score_diff = int(student_score - sc["predicted_score"])
            item = PredictionItem(
                school_name=sc["school_name"],
                predicted_score=sc["predicted_score"],
                admission_probability=sc["admission_probability"],
                admission_type=sc["admission_type"],
                score_diff=score_diff
            )
            grouped[sc["admission_type"]].append(item)

        # 排序：冲刺优先排名接近的（险中求），保底优先排名远高于录取线的
        def sort_key(item: PredictionItem, ad_type: str) -> tuple:
            prob = item.admission_probability
            if ad_type == "冲刺":
                # 冲刺：概率越高越好（排名越接近录取线）
                return (prob,)
            elif ad_type == "保底":
                # 保底：概率越高越好
                return (prob,)
            else:
                # 稳定：概率优先
                return (prob,)

        for ad_type in ["冲刺", "稳定", "保底"]:
            grouped[ad_type].sort(key=lambda x: sort_key(x, ad_type), reverse=True)
            grouped[ad_type] = grouped[ad_type][:self.TYPE_LIMITS[ad_type]]

        # 如果稳定为空，但有接近75%的学校，归为"稳定"
        if not grouped["稳定"] and school_data:
            # 找出概率在40%-75%之间且最接近75%的学校
            candidates = [sc for sc in school_data if 40 <= sc["admission_probability"] < 75]
            if candidates:
                best = max(candidates, key=lambda x: x["admission_probability"])
                grouped["稳定"] = [PredictionItem(
                    school_name=best["school_name"],
                    predicted_score=best["predicted_score"],
                    admission_probability=best["admission_probability"],
                    admission_type="稳定",
                    score_diff=int(student_score - best["predicted_score"])
                )]

        result_predictions = {
            "冲刺": grouped["冲刺"],
            "稳定": grouped["稳定"],
            "保底": grouped["保底"]
        }

        return StudentPrediction(
            student_id=student_id,
            current_score=student_score,
            current_ranking=current_ranking,
            predicted_ranking=student_predicted_rank,
            ranking_trend=ranking_trend,
            predictions=result_predictions
        )

    def _calculate_student_ability(self, records: list) -> dict:
        """计算学生能力值：平均分、稳定性、趋势"""
        if not records:
            return {"avg_score": 0, "ranking_stability": 0, "ranking_trend": "波动"}

        # 取最近5次考试记录
        recent = records[:5]
        scores = [float(r.score) for r in recent]
        rankings = [r.ranking for r in recent if r.ranking]

        # 平均分
        avg_score = statistics.mean(scores) if scores else 0

        # 排名稳定性（标准差，越大越不稳定）
        if len(rankings) >= 2:
            ranking_stability = statistics.stdev(rankings) if len(rankings) > 1 else 0
        else:
            ranking_stability = 0

        # 排名趋势
        if len(rankings) >= 3:
            first_rank = rankings[0]
            last_rank = rankings[-1]
            if first_rank < last_rank:  # 排名数字变小=进步
                ranking_trend = "上升"
            elif first_rank > last_rank:
                ranking_trend = "下降"
            else:
                ranking_trend = "波动"
        else:
            ranking_trend = "波动"

        return {
            "avg_score": avg_score,
            "ranking_stability": ranking_stability,
            "ranking_trend": ranking_trend
        }

    def _calculate_admission_probability(
        self,
        student_score: float,
        student_predicted_rank: int,
        ranking_stability: float,
        admission_rank: int,
        enrollment_count: int,
        target_score: float
    ) -> int:
        """计算录取概率
        核心逻辑：
        1. 先看分数差：学生分数超出学校分数线越多，概率越高
        2. 再看排名差：排名差距作为调整因子
        """

        # 1. 分数差计算
        score_gap = student_score - target_score
        if score_gap > 30:
            score_factor = 35  # 超出30+分 → 保底基础
        elif score_gap > 0:
            score_factor = 20  # 略超出 → 稳定
        elif score_gap > -30:
            score_factor = 0  # 略低于 → 稳定
        else:
            score_factor = -30  # 低于30+分 → 冲刺

        # 2. 排名差距调整
        rank_gap = student_predicted_rank - admission_rank
        if rank_gap > 3000:
            rank_factor = -20
        elif rank_gap > 1000:
            rank_factor = -10
        elif rank_gap > 300:
            rank_factor = 0
        elif rank_gap > -500:
            rank_factor = 5
        elif rank_gap > -2000:
            rank_factor = 10
        else:
            rank_factor = 15

        # 3. 稳定性调整
        if ranking_stability > 20:
            stability_factor = -8
        elif ranking_stability > 10:
            stability_factor = -3
        else:
            stability_factor = 3

        # 4. 招生人数影响
        if enrollment_count < 200:
            competition_factor = -3
        elif enrollment_count > 600:
            competition_factor = 3
        else:
            competition_factor = 0

        base_prob = 50 + score_factor + rank_factor
        final_prob = base_prob + stability_factor + competition_factor
        return max(10, min(95, final_prob))

    def _empty_prediction(self, student_id: int, student_score: float) -> StudentPrediction:
        return StudentPrediction(
            student_id=student_id,
            current_score=student_score,
            current_ranking=1,
            predicted_ranking=1,
            ranking_trend="波动",
            predictions={"冲刺": [], "稳定": [], "保底": []}
        )
