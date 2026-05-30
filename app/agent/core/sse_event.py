"""SSE 事件类型定义——7 种事件覆盖完整 Agent 生命周期。"""

from dataclasses import dataclass
from typing import Any
import json


class SSEEvent:
    """SSE 事件基类，提供序列化方法。"""

    def to_sse(self) -> str:
        return f"event: {self.type}\ndata: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"

    @property
    def type(self) -> str:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError


@dataclass
class ThinkingEvent(SSEEvent):
    text: str

    @property
    def type(self) -> str:
        return "thinking"

    def to_dict(self) -> dict:
        return {"text": self.text}


@dataclass
class ToolStartEvent(SSEEvent):
    tool: str
    args_summary: str

    @property
    def type(self) -> str:
        return "tool_start"

    def to_dict(self) -> dict:
        return {"tool": self.tool, "args_summary": self.args_summary}


@dataclass
class ToolEndEvent(SSEEvent):
    tool: str
    summary: str
    ok: bool = True

    @property
    def type(self) -> str:
        return "tool_end"

    def to_dict(self) -> dict:
        return {"tool": self.tool, "summary": self.summary, "ok": self.ok}


@dataclass
class TextDeltaEvent(SSEEvent):
    text: str

    @property
    def type(self) -> str:
        return "text_delta"

    def to_dict(self) -> dict:
        return {"text": self.text}


@dataclass
class DataCardEvent(SSEEvent):
    card_type: str
    title: str
    data_id: str | None = None
    inline_data: dict | None = None

    @property
    def type(self) -> str:
        return "data_card"

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"card_type": self.card_type, "title": self.title}
        if self.data_id is not None:
            d["data_id"] = self.data_id
        if self.inline_data is not None:
            d["inline_data"] = self.inline_data
        return d


@dataclass
class DoneEvent(SSEEvent):
    session_id: str
    message_id: int

    @property
    def type(self) -> str:
        return "done"

    def to_dict(self) -> dict:
        return {"session_id": self.session_id, "message_id": self.message_id}


@dataclass
class ErrorEvent(SSEEvent):
    message: str
    recoverable: bool = False

    @property
    def type(self) -> str:
        return "error"

    def to_dict(self) -> dict:
        return {"message": self.message, "recoverable": self.recoverable}