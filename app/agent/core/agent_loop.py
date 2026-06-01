"""Agent 执行引擎——A+B 混合循环，DeepSeek Function Calling + SSE 流式输出。

流程:
1. LLM Tool Selection（并行执行）
2. 规则自动审核（基于已拉取数据自动触发补充 tool）
3. LLM 审视（可选，最多额外 2 步）
4. LLM 流式生成 + Pydantic 校验
"""

import json
import time
from typing import AsyncGenerator
from sqlalchemy.orm import Session

from app.core.config import LLM_MAX_RETRIES
from app.core.llm_logger import log_llm
from app.agent.core.llm_client import chat_completion
from app.agent.core.prompt import build_system_prompt
from app.agent.core.sse_event import (
    ThinkingEvent,
    ToolStartEvent,
    ToolEndEvent,
    TextDeltaEvent,
    DataCardEvent,
    DoneEvent,
    ErrorEvent,
)
from app.agent.tools import execute_tools_parallel, TOOL_DEFINITIONS
from app.agent.schemas.suggestion import validate_llm_output
from app.agent.core.session_manager import SessionManager

DATA_CARD_TYPES = {
    "get_kp_mastery_rates": ("weak_kp", "薄弱知识点排名"),
    "get_kp_dependencies": ("kp_dependency", "前置依赖链"),
    "get_tiered_students": ("tiered_students", "四层分层名单"),
    "get_student_trend": ("student_trend", "学生趋势"),
    "get_advanced_students": ("advanced_students", "培优名单"),
    "get_remedial_students": ("remedial_students", "补差名单"),
    "get_class_trend_summary": ("class_trend", "班级趋势"),
    "get_enrollment_forecast": ("enrollment", "升学预估"),
    "get_class_rank_summary": ("class_rank", "排名汇总"),
    "get_question_quality": ("question_quality", "题目质量"),
}

MAX_DEEP_STEPS = 2
INLINE_SIZE_LIMIT = 5000


async def run_agent_loop(
    db: Session,
    sm: SessionManager,
    session_id: str,
    user_message: str,
    class_id: int,
    class_name: str,
) -> AsyncGenerator[str, None]:
    """Agent 执行主循环——A+B 混合模式，yield SSE 事件字符串。"""

    sm.db = db
    sm.add_message(session_id, "user", {"type": "text", "text": user_message})

    log_llm({
        "type": "user_message",
        "session_id": session_id,
        "content": user_message,
    })

    yield ThinkingEvent(text="正在分析你的问题...").to_sse()

    system_prompt = build_system_prompt(class_id, class_name)
    history = sm.get_messages(session_id, limit=20)
    messages = _build_llm_messages(system_prompt, history)

    try:
        response = await chat_completion(messages, tools=TOOL_DEFINITIONS, session_id=session_id)
    except Exception as e:
        log_llm({
            "type": "llm_error",
            "session_id": session_id,
            "error": f"LLM 调用失败: {e}",
        })
        yield ErrorEvent(message=f"LLM 调用失败: {e}", recoverable=False).to_sse()
        yield DoneEvent(session_id=session_id, message_id=-1).to_sse()
        return

    choice = response["choices"][0]
    initial_tool_calls = choice["message"].get("tool_calls", [])

    if not initial_tool_calls:
        content = choice["message"].get("content", "")
        if content:
            assistant_msg = sm.add_message(
                session_id, "assistant",
                {"type": "text", "text": content}
            )
            yield TextDeltaEvent(text=content).to_sse()
            yield DoneEvent(session_id=session_id, message_id=assistant_msg.id).to_sse()
            return
        yield TextDeltaEvent(text="抱歉，我无法理解你的分析需求，请换一种方式描述试试。").to_sse()
        yield DoneEvent(session_id=session_id, message_id=-1).to_sse()
        return

    all_tool_results = []
    for tc in initial_tool_calls:
        fn = tc["function"]
        tool_name = fn["name"]
        args = fn.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        yield ToolStartEvent(tool=tool_name, args_summary=_brief_args(tool_name, args)).to_sse()
        t0 = time.time()

        try:
            result_list = await execute_tools_parallel([tc], db, class_id, session_id=session_id)
            r = result_list[0]
            r["params"] = args
            r["duration_ms"] = int((time.time() - t0) * 1000)
            yield ToolEndEvent(tool=tool_name, summary=r["summary"], ok=True).to_sse()
            all_tool_results.append(r)
        except Exception as e:
            yield ToolEndEvent(tool=tool_name, summary=str(e), ok=False).to_sse()
            log_llm({
                "type": "tool_result",
                "session_id": session_id,
                "tool": tool_name,
                "summary": str(e),
                "ok": False,
                "params": args,
                "duration_ms": 0,
            })
            all_tool_results.append({
                "tool_name": tool_name,
                "summary": str(e),
                "data_id": None,
                "full_data": None,
                "ok": False,
                "params": args,
                "duration_ms": 0,
            })

    # 规则自动审核
    triggered = await _check_rule_triggers(all_tool_results, db, class_id)
    for t in triggered:
        yield ToolStartEvent(tool=t["tool_name"], args_summary="(规则自动触发)").to_sse()
        yield ToolEndEvent(tool=t["tool_name"], summary=t["summary"], ok=True).to_sse()
    all_tool_results.extend(triggered)

    # LLM 审视（可选，最多额外 2 步）
    deep_count = 0
    while deep_count < MAX_DEEP_STEPS:
        tool_data_text = "\n".join(
            f"[{r['tool_name']}]: {r['summary']}" for r in all_tool_results
        )
        check_prompt = messages + [
            {"role": "user", "content": f"已获取以下数据:\n{tool_data_text}\n\n如果数据足够生成教学建议，回复 DONE。如需更多数据，调用 tool。"}
        ]

        try:
            check_response = await chat_completion(check_prompt, tools=TOOL_DEFINITIONS, session_id=session_id)
        except Exception:
            break

        choice2 = check_response["choices"][0]
        if choice2["finish_reason"] == "stop":
            break

        extra_calls = choice2["message"].get("tool_calls", [])
        if not extra_calls:
            break

        deep_count += 1
        for tc in extra_calls:
            fn = tc["function"]
            tool_name = fn["name"]
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)
            yield ToolStartEvent(tool=tool_name, args_summary=f"(第{deep_count}步深入)").to_sse()
            t0 = time.time()
            try:
                result_list = await execute_tools_parallel([tc], db, class_id, session_id=session_id)
                r = result_list[0]
                r["params"] = args
                r["duration_ms"] = int((time.time() - t0) * 1000)
                yield ToolEndEvent(tool=tool_name, summary=r["summary"], ok=True).to_sse()
                all_tool_results.append(r)
            except Exception as e:
                yield ToolEndEvent(tool=tool_name, summary=str(e), ok=False).to_sse()
                log_llm({
                    "type": "tool_result",
                    "session_id": session_id,
                    "tool": tool_name,
                    "summary": str(e),
                    "ok": False,
                    "params": args,
                    "duration_ms": 0,
                })
                all_tool_results.append({
                    "tool_name": tool_name, "summary": str(e),
                    "data_id": None, "full_data": None, "ok": False,
                    "params": args, "duration_ms": 0,
                })

    # LLM 流式生成——将 tool 结果作为 user 消息内容注入，避免 DeepSeek tool 消息约束
    tool_data_text = "基于以下分析数据生成教学报告:\n" + "\n".join(
        f"[{r['tool_name']}]: {r['summary']}" for r in all_tool_results
    )
    final_messages = messages + [
        {"role": "user", "content": f"{user_message}\n\n已获取分析数据:\n{tool_data_text}"}
    ]

    assistant_msg = sm.add_message(
        session_id, "assistant",
        {"type": "mixed", "text": "", "data_card_ids": [], "tool_call_ids": []}
    )

    for tr in all_tool_results:
        sm.add_tool_call(
            message_id=assistant_msg.id,
            tool_name=tr["tool_name"],
            params=tr.get("params", {}),
            summary=tr["summary"],
            data_id=tr.get("data_id"),
            error=None if tr.get("ok", True) else tr.get("summary"),
            duration_ms=tr.get("duration_ms", 0),
        )

    for tr in all_tool_results:
        if tr.get("data_id") and tr.get("tool_name") in DATA_CARD_TYPES:
            card_type, title = DATA_CARD_TYPES[tr["tool_name"]]
            full_data = tr.get("full_data")
            if full_data and _json_size(full_data) <= INLINE_SIZE_LIMIT:
                yield DataCardEvent(card_type=card_type, title=title, inline_data=full_data).to_sse()
            else:
                yield DataCardEvent(card_type=card_type, title=title, data_id=tr["data_id"]).to_sse()

    try:
        # 先用非流式获取，再逐字 yield
        response = await chat_completion(final_messages, session_id=session_id)
        full_text = response["choices"][0]["message"]["content"]
        # 按句子/短语切分输出，模拟流式体验
        import re
        chunks = re.split(r'(\n\n|。|；|，|、|\n)', full_text)
        for chunk in chunks:
            if chunk:
                yield TextDeltaEvent(text=chunk).to_sse()

        validated = await _validate_with_retry(final_messages, full_text, session_id=session_id)
        if validated:
            assistant_msg.content_json["text"] = json.dumps(validated, ensure_ascii=False)
        else:
            assistant_msg.content_json["text"] = full_text

        log_llm({
            "type": "assistant_text",
            "session_id": session_id,
            "content": full_text,
        })

        assistant_msg.content_json["data_card_ids"] = [
            tr["data_id"] for tr in all_tool_results if tr.get("data_id")
        ]
        db.commit()
    except Exception as e:
        log_llm({
            "type": "llm_error",
            "session_id": session_id,
            "error": f"生成失败: {e}",
        })
        yield ErrorEvent(message=f"生成失败: {e}", recoverable=False).to_sse()

    yield DoneEvent(session_id=session_id, message_id=assistant_msg.id).to_sse()


# ── 内部辅助函数 ──────────────────────────────────

def _build_llm_messages(system_prompt: str, history: list) -> list[dict]:
    msgs = [{"role": "system", "content": system_prompt}]
    for msg in history[-20:]:
        role = msg.role
        content = msg.content_json
        if role == "user":
            msgs.append({"role": "user", "content": content.get("text", "")})
        elif role == "assistant":
            msgs.append({"role": "assistant", "content": content.get("text", "")})
    return msgs


def _format_tool_results(results: list[dict]) -> list[dict]:
    return [
        {
            "role": "tool",
            "tool_call_id": r.get("tool_call_id", "unknown"),
            "content": r["summary"],
        }
        for r in results
    ]


def _brief_args(tool_name: str, args: dict) -> str:
    """生成工具参数的简短摘要。"""
    if "exam_ids" in args:
        return f"exam_ids={args['exam_ids']}"
    if "exam_id" in args:
        return f"exam_id={args['exam_id']}"
    if "student_no" in args:
        return f"student_no={args['student_no']}"
    if "kp_id" in args:
        return f"kp_id={args['kp_id']}"
    return "..."


async def _check_rule_triggers(
    results: list[dict], db, class_id: int
) -> list[dict]:
    """规则审核：基于已拉取数据自动触发补充 tool 调用。"""
    triggered = []
    for r in results:
        if r.get("tool_name") == "get_kp_mastery_rates" and r.get("ok"):
            data = r.get("full_data", {})
            weak_kps = [
                kp for kp in data.get("knowledge_points", [])
                if kp.get("mastery_rate", 1) < 0.60
            ]
            if weak_kps:
                from app.agent.tools.data_tools import _get_kp_dependencies
                for kp in weak_kps[:3]:
                    result = await _get_kp_dependencies({"kp_id": kp["kp_id"]}, db)
                    result["tool_name"] = "get_kp_dependencies"
                    result["ok"] = True
                    triggered.append(result)
    return triggered


async def _validate_with_retry(
    messages: list[dict], first_response: str, session_id: str | None = None
) -> dict | None:
    for attempt in range(int(LLM_MAX_RETRIES) + 1):
        try:
            data = json.loads(first_response) if attempt == 0 else {}
            if attempt > 0:
                retry_msg = "上一条回复格式不符合要求，请严格按 JSON Schema 输出。"
                messages.append({"role": "user", "content": retry_msg})
                response = await chat_completion(messages, session_id=session_id)
                data = json.loads(response["choices"][0]["message"]["content"])

            validated = validate_llm_output(data)
            if validated:
                return validated.model_dump()
        except (json.JSONDecodeError, Exception):
            continue
    return None


def _json_size(data: dict) -> int:
    try:
        return len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    except Exception:
        return 9999
