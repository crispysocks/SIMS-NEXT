# -*- coding: utf-8 -*-
"""
LLM API 客户端封装

提供 OpenAI API 的调用接口，支持重试机制。
"""

from openai import OpenAI
import json
import os

# 常量定义
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_RETRIES = 2

# OpenAI 客户端初始化
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL") or None
)


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

    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "timeout": timeout
    }

    # 如果 response_format 是 json_object，添加 response_format 参数
    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content

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