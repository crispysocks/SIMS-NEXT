"""Tool 注册表——所有 10 个 Tool 的 OpenAI Function Calling 定义 + 执行调度。

B2 阶段将添加 ALL_TOOLS dict 和 execute 函数。
"""

# OpenAI Function Calling 格式的 Tool 定义列表
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_kp_mastery_rates",
            "description": "查询指定班级在一次或多次考试中各知识点的掌握率排名，返回班级得分率、年级偏差、区分度",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "班级 ID"},
                    "exam_ids": {"type": "array", "items": {"type": "integer"}, "description": "考试 ID 列表 (如 [1,2,3])"},
                    "kp_ids": {"type": "array", "items": {"type": "integer"}, "description": "可选: 限定知识点 ID 范围"},
                },
                "required": ["class_id", "exam_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_kp_dependencies",
            "description": "查询某个知识点的前置依赖关系链（如因式分解 → 二次函数），用于根因分析",
            "parameters": {
                "type": "object",
                "properties": {
                    "kp_id": {"type": "integer", "description": "知识点 ID"},
                },
                "required": ["kp_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tiered_students",
            "description": "获取某次考试的四层分层名单（A/B/C/D 层）及每层统计摘要",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "班级 ID"},
                    "exam_id": {"type": "integer", "description": "考试 ID"},
                },
                "required": ["class_id", "exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_trend",
            "description": "查询指定学生在历次考试中某知识点的得分率变化趋势",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_no": {"type": "string", "description": "学号"},
                    "kp_id": {"type": "integer", "description": "知识点 ID（可选，不传则查总分趋势）"},
                    "exam_ids": {"type": "array", "items": {"type": "integer"}, "description": "考试 ID 列表"},
                },
                "required": ["student_no", "exam_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_advanced_students",
            "description": "获取培优名单——总分排名前 30% 但存在薄弱知识点的学生",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "班级 ID"},
                    "exam_id": {"type": "integer", "description": "考试 ID"},
                },
                "required": ["class_id", "exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_remedial_students",
            "description": "获取补差名单——总分排名后 30% 且多个核心知识点薄弱的学生",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "班级 ID"},
                    "exam_id": {"type": "integer", "description": "考试 ID"},
                },
                "required": ["class_id", "exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_class_trend_summary",
            "description": "获取班级在多次考试中的均分走势和知识点掌握率变化趋势",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "班级 ID"},
                    "exam_ids": {"type": "array", "items": {"type": "integer"}, "description": "考试 ID 列表"},
                },
                "required": ["class_id", "exam_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_enrollment_forecast",
            "description": "升学形势分析——基于近几次考试预测上线率和临界生（仅初三）",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "班级 ID"},
                    "target_score_line": {"type": "number", "description": "目标分数线（百分制，默认 65）"},
                },
                "required": ["class_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_class_rank_summary",
            "description": "获取班级前 N 名学生的知识点掌握汇总 + 共同薄弱点",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "班级 ID"},
                    "exam_id": {"type": "integer", "description": "考试 ID"},
                    "top_n": {"type": "integer", "description": "前 N 名（默认 10）"},
                },
                "required": ["class_id", "exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_question_quality",
            "description": "分析某次考试题目的区分度和难度系数，标注低质量题目",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "integer", "description": "考试 ID"},
                    "question_ids": {"type": "array", "items": {"type": "integer"}, "description": "可选: 限定题目 ID"},
                },
                "required": ["exam_id"],
            },
        },
    },
]

# 注册所有 Tool 函数
from app.agent.tools.data_tools import DATA_TOOLS
from app.agent.tools.analysis_tools import ANALYSIS_TOOLS

ALL_TOOLS = {**DATA_TOOLS, **ANALYSIS_TOOLS}


async def execute_tool(
    tool_name: str, args: dict, db, class_id: int
) -> dict:
    """执行单个 Tool 并返回 {summary, data_id, full_data, ok}。

    class_id 由 session 绑定注入，覆盖 LLM 传入的参数，防止越权。
    """
    if tool_name not in ALL_TOOLS:
        return {"summary": f"未知工具: {tool_name}", "data_id": None, "ok": False}

    args["class_id"] = class_id
    return await ALL_TOOLS[tool_name](args, db)


async def execute_tools_parallel(
    tool_calls: list[dict], db, class_id: int
) -> list[dict]:
    """并行执行多个 Tool 调用。"""
    import asyncio

    async def run_one(tc: dict):
        fn = tc["function"]
        args = fn.get("arguments", {})
        if isinstance(args, str):
            import json
            args = json.loads(args)
        result = await execute_tool(fn["name"], args, db, class_id)
        result["tool_name"] = fn["name"]
        result["tool_call_id"] = tc.get("id")
        return result

    return await asyncio.gather(*[run_one(tc) for tc in tool_calls])
