"""综合报告生成（F6）——异步执行分析 + LLM 生成 + 存储结果。"""

import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.agent.core.llm_client import chat_completion
from app.agent.schemas.suggestion import validate_llm_output
from app.core.config import LLM_MAX_RETRIES

task_store: dict[str, dict] = {}


async def submit_report_task(
    db: Session,
    class_id: int,
    class_name: str,
    exam_ids: list[int],
    modules: list[str],
) -> str:
    """提交报告生成任务，返回 task_id。"""
    task_id = str(uuid.uuid4())
    task_store[task_id] = {
        "status": "processing",
        "progress": 0,
        "result": None,
        "created_at": datetime.utcnow().isoformat(),
    }

    import asyncio
    asyncio.create_task(
        _generate_report(task_id, db, class_id, class_name, exam_ids, modules)
    )
    return task_id


def get_task_status(task_id: str) -> dict | None:
    return task_store.get(task_id)


async def _generate_report(
    task_id: str,
    db: Session,
    class_id: int,
    class_name: str,
    exam_ids: list[int],
    modules: list[str],
) -> None:
    try:
        task_store[task_id]["progress"] = 20

        from app.agent.tools import ALL_TOOLS
        structured_data = {}
        tool_results = []

        module_tool_map = {
            "weak-points": "get_kp_mastery_rates",
            "trends": "get_class_trend_summary",
            "enrollment": "get_enrollment_forecast",
            "tiered-teaching": "get_tiered_students",
            "student-lists": "get_advanced_students",
        }

        for module in modules:
            tool_name = module_tool_map.get(module)
            if not tool_name or tool_name not in ALL_TOOLS:
                continue
            args = {"class_id": class_id}
            if module == "enrollment":
                args["target_score_line"] = 65
            elif module in ("tiered-teaching", "student-lists"):
                args["exam_id"] = exam_ids[-1] if exam_ids else None
            else:
                args["exam_ids"] = exam_ids

            try:
                result = await ALL_TOOLS[tool_name](args, db)
                structured_data[module] = result.get("full_data", {})
                if result.get("summary"):
                    tool_results.append(result["summary"])
            except Exception:
                structured_data[module] = {}

        task_store[task_id]["progress"] = 50

        system_prompt = f"""你是教研组长，请基于以下班级数据生成正式的教学优化报告。

## 班级信息
{class_name}，分析范围: 考试 {exam_ids}

## 分析数据
{json.dumps({k: str(v)[:500] for k, v in structured_data.items()}, ensure_ascii=False)}

## 输出要求
严格输出 JSON，格式参考 AnalysisReport Schema。"""

        for attempt in range(int(LLM_MAX_RETRIES) + 1):
            try:
                response = await chat_completion([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请生成教学优化报告"},
                ])
                content = response["choices"][0]["message"]["content"]
                data = json.loads(content)
                validated = validate_llm_output(data)
                if validated:
                    task_store[task_id] = {
                        "status": "completed",
                        "progress": 100,
                        "result": {
                            "structured_data": structured_data,
                            "report": validated.model_dump(),
                        },
                        "created_at": task_store[task_id]["created_at"],
                    }
                    return
            except Exception:
                continue

        # 降级
        task_store[task_id] = {
            "status": "completed",
            "progress": 100,
            "result": {
                "structured_data": structured_data,
                "report": {"overall_direction": "LLM 生成失败，以下是统计数据。", "weak_kp_remediation": []},
                "fallback": True,
            },
            "created_at": task_store[task_id]["created_at"],
        }
    except Exception as e:
        task_store[task_id] = {
            "status": "failed",
            "progress": 0,
            "result": {"error": str(e)},
            "created_at": task_store[task_id].get("created_at", datetime.utcnow().isoformat()),
        }
