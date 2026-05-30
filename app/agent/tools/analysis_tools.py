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


async def _get_class_ranking(args: dict, db) -> dict:
    """获取某班级在年级中的排名（按考试类型，如'期中考试'）。"""
    repo = ScoreRecordRepo(db)
    exam_type = args.get("exam_type", "期中考试")
    class_id = args.get("class_id")
    semester = args.get("semester")

    all_classes = repo.get_all_class_exam_avgs_by_type(exam_type, semester)

    if not all_classes:
        return {"summary": f"暂无 {exam_type} 的年级数据", "data_id": None, "full_data": None, "ok": True}

    my_class = next((c for c in all_classes if c["class_id"] == class_id), None)
    total = len(all_classes)
    rank = my_class["rank"] if my_class else None

    data_id = str(uuid.uuid4())
    rank_lines = "\n".join(
        f"第{c['rank']}名: {c['class_id']}班 均分{c['avg_score']} 得分率{c['avg_rate']}%"
        for c in all_classes
    )
    if my_class:
        summary = f"{exam_type}年级排名: {class_id}班第{rank}/{total}名（均分{my_class['avg_score']}，得分率{my_class['avg_rate']}%）\n{rank_lines}"
    else:
        summary = f"{exam_type}年级排名（共{total}个班）:\n{rank_lines}"

    return {
        "summary": summary,
        "data_id": data_id,
        "full_data": {"exam_type": exam_type, "class_id": class_id, "ranking": all_classes},
        "ok": True,
    }


async def _get_kp_class_comparison(args: dict, db) -> dict:
    """对比各班在指定知识点上的掌握率。"""
    repo = ScoreRecordRepo(db)
    exam_type = args.get("exam_type", "期中考试")
    kp_ids = args.get("kp_ids")
    semester = args.get("semester")

    kp_data = repo.get_grade_kp_mastery_by_type(exam_type, kp_ids, semester)

    if not kp_data:
        return {"summary": f"暂无 {exam_type} 的知识点对比数据", "data_id": None, "full_data": None, "ok": True}

    data_id = str(uuid.uuid4())
    summary_parts = [f"{exam_type}各班知识点掌握率对比:"]
    for kp in kp_data[:10]:
        class_rates = "、".join(
            f"{cid}班{rate:.0%}" for cid, rate in sorted(kp["classes"].items())
        )
        summary_parts.append(f"  {kp['kp_name']}: {class_rates}")

    summary = "\n".join(summary_parts)
    return {
        "summary": summary,
        "data_id": data_id,
        "full_data": {"exam_type": exam_type, "kp_comparison": kp_data},
        "ok": True,
    }


ANALYSIS_TOOLS = {
    "get_class_trend_summary": _get_class_trend_summary,
    "get_enrollment_forecast": _get_enrollment_forecast,
    "get_class_rank_summary": _get_class_rank_summary,
    "get_question_quality": _get_question_quality,
    "get_class_ranking": _get_class_ranking,
    "get_kp_class_comparison": _get_kp_class_comparison,
}
