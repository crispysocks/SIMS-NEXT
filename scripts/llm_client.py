# -*- coding: utf-8 -*-
"""
LLM API 客户端封装

提供 OpenAI API 的调用接口，支持重试机制。
"""

from openai import OpenAI
import json
import os
import time

# 常量定义
DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
MAX_RETRIES = 2

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
)

# 尝试导入 LLM 日志记录器（脚本环境可能没有 app 包）
try:
    from app.core.llm_logger import log_llm
    _has_llm_logger = True
except ImportError:
    _has_llm_logger = False


def _try_log(record: dict):
    """尝试记录日志，导入失败时静默跳过。"""
    if _has_llm_logger:
        try:
            log_llm(record)
        except Exception:
            pass


def call_llm(prompt: str, model: str = DEFAULT_MODEL, response_format: str = "json_object", timeout: int = 60) -> dict:
    """
    调用 LLM API

    Args:
        prompt: 输入提示词
        model: 模型名称
        response_format: 返回格式 (json_object / text)
        timeout: 请求超时时间（秒）

    Returns:
        dict: LLM 返回的 JSON 解析结果

    Raises:
        ValueError: 当 prompt 为空或 None 时
    """
    if not prompt or not prompt.strip():
        return {"error": "prompt is empty or None"}

    messages = [{"role": "user", "content": prompt}]
    kwargs = {
        "model": model,
        "messages": messages,
        "timeout": timeout
    }

    # 如果 response_format 是 json_object，添加 response_format 参数
    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}

    t0 = time.time()
    _try_log({
        "type": "llm_request",
        "model": model,
        "messages": messages,
    })

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        _try_log({
            "type": "llm_error",
            "model": model,
            "error": str(e),
            "latency_ms": int((time.time() - t0) * 1000),
        })
        raise

    content = response.choices[0].message.content
    _try_log({
        "type": "llm_response",
        "model": model,
        "content": content,
        "usage": getattr(response, "usage", None),
        "latency_ms": int((time.time() - t0) * 1000),
    })

    # 尝试解析 JSON，处理可能包含非 JSON 前缀/后缀的情况
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试清理并提取 JSON
        content = content.strip()

        # 查找 JSON 数组或对象的起始和结束位置
        start_idx = content.find('[')
        if start_idx == -1:
            start_idx = content.find('{')

        if start_idx != -1:
            # 找到 JSON 的起始位置，尝试从那里开始解析
            json_str = content[start_idx:]
            # 找到匹配的结束括号
            if json_str.startswith('['):
                # 对于数组，找到对应的结束 ]
                depth = 0
                for i, c in enumerate(json_str):
                    if c == '[':
                        depth += 1
                    elif c == ']':
                        depth -= 1
                        if depth == 0:
                            json_str = json_str[:i+1]
                            break
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return {"error": f"failed to parse JSON response: {content[:500]}"}


def call_llm_with_retry(prompt: str, model: str = DEFAULT_MODEL, max_retries: int = MAX_RETRIES, response_format: str = "json_object", timeout: int = 60) -> dict:
    """
    带重试的 LLM 调用

    Args:
        prompt: 输入提示词
        model: 模型名称
        max_retries: 最大重试次数
        response_format: 返回格式 (json_object / text)
        timeout: 请求超时时间（秒）

    Returns:
        dict: LLM 返回的 JSON 解析结果
    """
    for attempt in range(max_retries):
        try:
            return call_llm(prompt, model, response_format, timeout)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return {"error": f"max retries exceeded: {e}"}
        except Exception as e:
            print(f"Warning: LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return {"error": f"max retries exceeded: {e}"}
    return {"error": "max retries exceeded"}