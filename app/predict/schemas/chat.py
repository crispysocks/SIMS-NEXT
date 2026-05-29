from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: Optional[str] = None  # 追问内容，首轮为空
    stream: bool = True


class ChatStreamEvent(BaseModel):
    content: str
    done: bool = False