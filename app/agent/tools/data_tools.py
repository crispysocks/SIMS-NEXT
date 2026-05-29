"""数据查询类 Tool —— 6 个，每个返回 {summary, data_id, full_data}。"""

import uuid
from app.agent.services.weak_point_engine import WeakPointEngine
from app.agent.services.tier_engine import TierEngine
from app.agent.services.student_list_engine import StudentListEngine
from app.agent.services.kp_comparison_engine import KPComparisonEngine
from app.agent.repositories.knowledge_point_repo import KnowledgePointRepo


async def _get_kp_mastery_rates(args: dict, db) -> dict:
    engine = WeakPointEngine(db)
    result = engine.analyze(
        class_id=args["class_id"],
        exam_ids=args["exam_ids"],
        kp_ids=args.get("kp_ids"),
    )
    data_id = str(uuid.uuid4())
    kp_count = len(result.get("knowledge_points", []))
    top3 = result.get("knowledge_points", [])[:3]
    top3_str = "、".join(
        f"{kp['name']}({kp['mastery_rate']:.0%})" for kp in top3
    ) if top3 else "无"
    return {
        "summary": f"获取 {kp_count} 个知识点掌握率数据，薄弱 Top3: {top3_str}",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


async def _get_kp_dependencies(args: dict, db) -> dict:
    repo = KnowledgePointRepo(db)
    kp_id = args.get("kp_id") or args.get("kp_id")
    deps = repo.get_dependencies(kp_id)
    data_id = str(uuid.uuid4())
    dep_count = len(deps)
    chain = " → ".join(d["source_name"] for d in deps[:5])
    return {
        "summary": f"发现 {dep_count} 条前置依赖: {chain}" if dep_count else "该知识点无前置依赖记录",
        "data_id": data_id,
        "full_data": {"dependencies": deps, "kp_id": kp_id},
        "ok": True,
    }


async def _get_tiered_students(args: dict, db) -> dict:
    engine = TierEngine(db)
    result = engine.analyze(class_id=args["class_id"], exam_id=args["exam_id"])
    data_id = str(uuid.uuid4())
    tiers = result.get("tiers", {})
    tier_summary = "、".join(
        f"{label}层{t.get('headcount', 0)}人(均分{t.get('avg_score', 0):.1f})"
        for label, t in tiers.items()
    )
    return {
        "summary": f"分层结果: {tier_summary}",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


async def _get_student_trend(args: dict, db) -> dict:
    engine = KPComparisonEngine(db)
    result = engine.get_student_trend(
        student_no=args["student_no"],
        exam_ids=args["exam_ids"],
        kp_id=args.get("kp_id"),
    )
    data_id = str(uuid.uuid4())
    trend = result.get("trend", "stable")
    trend_cn = {"rising": "上升", "falling": "下降", "volatile": "波动", "stable": "平稳"}.get(trend, "平稳")
    return {
        "summary": f"学生 {args['student_no']} 趋势: {trend_cn}",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


async def _get_advanced_students(args: dict, db) -> dict:
    engine = StudentListEngine(db)
    result = engine.get_advanced(class_id=args["class_id"], exam_id=args["exam_id"])
    data_id = str(uuid.uuid4())
    count = len(result.get("students", []))
    return {
        "summary": f"培优名单: {count} 人有潜力可挖",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


async def _get_remedial_students(args: dict, db) -> dict:
    engine = StudentListEngine(db)
    result = engine.get_remedial(class_id=args["class_id"], exam_id=args["exam_id"])
    data_id = str(uuid.uuid4())
    count = len(result.get("students", []))
    return {
        "summary": f"补差名单: {count} 人需要帮扶",
        "data_id": data_id,
        "full_data": result,
        "ok": True,
    }


DATA_TOOLS = {
    "get_kp_mastery_rates": _get_kp_mastery_rates,
    "get_kp_dependencies": _get_kp_dependencies,
    "get_tiered_students": _get_tiered_students,
    "get_student_trend": _get_student_trend,
    "get_advanced_students": _get_advanced_students,
    "get_remedial_students": _get_remedial_students,
}
