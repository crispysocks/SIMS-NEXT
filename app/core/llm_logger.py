"""LLM 调用历史记录器——将所有 LLM 交互（用户消息、模型响应、工具调用等）写入结构化日志。

日志策略:
- 带 session_id 的记录 → logs/conversations/{session_id}.log（每个对话一个文件）
- 不带 session_id 的记录 → logs/llm-YYYY-MM-DD.log（每日汇总，如 embedding 等非会话级调用）

日志格式：每行一个 JSON 对象 (JSON Lines)。
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

CONVERSATIONS_DIR = LOG_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(exist_ok=True)

MAX_LOG_FILES = 30

_lock = threading.Lock()


def _cleanup_old_logs():
    """清理超过 MAX_LOG_FILES 天的旧每日日志文件。"""
    files = sorted(LOG_DIR.glob("llm-*.log"), key=os.path.getmtime, reverse=True)
    for f in files[MAX_LOG_FILES:]:
        try:
            f.unlink()
        except OSError:
            pass


def _get_daily_log_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"llm-{today}.log"


def _get_session_log_path(session_id: str) -> Path:
    # 清理 session_id 中的非法文件名字符
    safe_id = "".join(c for c in session_id if c.isalnum() or c in "_-.")
    return CONVERSATIONS_DIR / f"{safe_id}.log"


def _write_line(path: Path, line: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def log_llm(record: dict):
    """写入一条 LLM 交互记录。

    如果 record 中包含 session_id，写入该会话专属的日志文件；
    否则写入每日汇总日志。

    Args:
        record: 包含 type 字段的字典，常见 type:
            - llm_request:   发送给 LLM 的请求（messages, tools, model）
            - llm_response:   LLM 返回的响应（content, tool_calls, usage, latency_ms）
            - llm_error:      LLM 调用异常（error, latency_ms）
            - user_message:   用户发送的消息（session_id, content）
            - tool_call:      工具调用（tool, args）
            - tool_result:    工具执行结果（tool, summary, ok, duration_ms）
            - embedding:      嵌入请求（model, text_length, dimensions, latency_ms）
            - assistant_text: 助手文本回复（session_id, content）
    """
    record["timestamp"] = datetime.now().isoformat()
    line = json.dumps(record, ensure_ascii=False) + "\n"

    session_id = record.get("session_id")

    with _lock:
        if session_id:
            _write_line(_get_session_log_path(session_id), line)
        else:
            _write_line(_get_daily_log_path(), line)

    _cleanup_old_logs()
