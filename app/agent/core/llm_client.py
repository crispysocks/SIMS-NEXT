"""LLM 客户端——封装 DeepSeek API 调用，兼容 OpenAI SDK 格式。

通过配置切换 base_url 可切换到任何 OpenAI 兼容的模型服务。
"""

from openai import AsyncOpenAI
from app.core.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT
from app.agent.tools import TOOL_DEFINITIONS


_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """获取全局 LLM 客户端单例。"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
            timeout=LLM_TIMEOUT,
        )
    return _client


async def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_choice: str = "auto",
    stream: bool = False,
    model: str | None = None,
) -> dict:
    """调用 LLM Chat Completion。

    Args:
        messages: 对话历史（含 System Prompt）
        tools: Tool 定义列表，为 None 时不启用 Function Calling
        tool_choice: "auto" / "none" / "required"
        stream: 是否流式返回
        model: 模型名称，默认使用配置值

    Returns:
        OpenAI 格式的 completion response dict
    """
    client = get_client()
    kwargs = {
        "model": model or LLM_MODEL,
        "messages": messages,
        "temperature": 0.3,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    if stream:
        kwargs["stream"] = True
        return await client.chat.completions.create(**kwargs)

    response = await client.chat.completions.create(**kwargs)
    return response.model_dump()


async def extract_tool_calls(messages: list[dict]) -> list[dict]:
    """向 LLM 发送消息并提取 tool_calls。

    Args:
        messages: 完整对话上下文（含 System Prompt + 历史 + 用户消息）

    Returns:
        [{id, function: {name, arguments}}, ...]
    """
    response = await chat_completion(messages, tools=TOOL_DEFINITIONS, tool_choice="auto")
    choice = response["choices"][0]
    if choice["finish_reason"] == "tool_calls":
        return choice["message"].get("tool_calls", [])
    return []
