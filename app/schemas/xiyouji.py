from typing import Optional
from pydantic import BaseModel, Field
from typing import Literal


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID（客户端生成）")
    message: str = Field(..., description="用户消息")
    history: list[Message] | None = Field(default=None, description="历史对话（可选）")


class ChatResponse(BaseModel):
    think: str | None = None
    reply: str
    personality: str | None = None
    emotion: str | None = None
    tone: str | None = None
    examples: list[dict] | None = Field(default=None, description="RAG检索到的示例文本")
