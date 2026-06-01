"""LLM 调用历史记录器——将所有 LLM 交互（用户消息、模型响应、工具调用等）写入结构化日志。

日志文件格式: logs/llm-YYYY-MM-DD.log，每行一个 JSON 对象。
自动按日轮转，保留最近 30 天。
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
MAX_LOG_FILES = 30

_lock = threading.Lock()


def _cleanup_old_logs():
    """清理超过 MAX_LOG_FILES 天的旧日志文件。"""
    files = sorted(LOG_DIR.glob("llm-*.log"), key=os.path.getmtime, reverse=True)
    for f in files[MAX_LOG_FILES:]:
        try:
            f.unlink()
        except OSError:
            pass


def _get_log_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"llm-{today}.log"


def log_llm(record: dict):
    """写入一条 LLM 交互记录。

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
    with _lock:
        path = _get_log_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    _cleanup_old_logs()
