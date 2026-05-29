"""统计分析类 Tool —— 4 个，每个返回 {summary, data_id, full_data}。"""

import uuid
from app.agent.services.trend_engine import TrendEngine
from app.agent.services.enrollment_engine import EnrollmentEngine
from app.agent.services.question_quality import QuestionQualityService
from app.agent.repositories.score_record_repo import ScoreRecordRepo


async def _get_class_trend_summary(args: dict, db) -> dict:
    engine = TrendEngine(db)
    result = engine.analyze(class_id=args["class_id"], exam_ids=args["exam_ids"])
    data_id = str(uuid.uuid4())
    exam_count = len(args["exam_ids"])
    direction = result.get("direction", "持平")
    slope = result.get("slope", 0)
    return {
        "summary": f"基于 {exam_count} 次考试趋势分析: 班级整体走势 {direction}（斜率 {slope:.2f}）",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


async def _get_enrollment_forecast(args: dict, db) -> dict:
    engine = EnrollmentEngine(db)
    result = engine.analyze(
        class_id=args["class_id"],
        target_score_line=args.get("target_score_line", 65),
    )
    data_id = str(uuid.uuid4())
    rate = result.get("enrollment_rate", 0)
    borderline = len(result.get("borderline_students", []))
    risk = len(result.get("risk_students", []))
    return {
        "summary": f"预估上线率 {rate:.0%}，临界生 {borderline} 人，高风险 {risk} 人",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


async def _get_class_rank_summary(args: dict, db) -> dict:
    repo = ScoreRecordRepo(db)
    exam_id = args["exam_id"]
    top_n = args.get("top_n", 10)
    result = repo.get_top_students_summary(
        class_id=args["class_id"], exam_id=exam_id, top_n=top_n
    )
    data_id = str(uuid.uuid4())
    common_weak = result.get("common_weak_kps", [])
    weak_str = "、".join(kp["kp_name"] for kp in common_weak[:3]) if common_weak else "无"
    return {
        "summary": f"前 {top_n} 名学生均分 {result.get('avg_score', 0):.1f}，共同薄弱点: {weak_str}",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


async def _get_question_quality(args: dict, db) -> dict:
    service = QuestionQualityService(db)
    exam_id = args["exam_id"]
    result = service.analyze(exam_id=exam_id, question_ids=args.get("question_ids"))
    data_id = str(uuid.uuid4())
    low_quality = [q for q in result.get("questions", []) if q.get("quality_label") == "低质量"]
    return {
        "summary": f"题目质量分析: {len(result.get('questions', []))} 题，其中 {len(low_quality)} 题区分度低",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


ANALYSIS_TOOLS = {
    "get_class_trend_summary": _get_class_trend_summary,
    "get_enrollment_forecast": _get_enrollment_forecast,
    "get_class_rank_summary": _get_class_rank_summary,
    "get_question_quality": _get_question_quality,
}
