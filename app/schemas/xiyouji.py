from typing import Optional, Literal
from pydantic import BaseModel, Field


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


class JourneyStartRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID")


class JourneyChoiceRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    choice: str = Field(..., description="用户选择的描述")


class KnowledgeCard(BaseModel):
    title: str
    content: str


class Achievement(BaseModel):
    id: str
    name: str
    description: str
    unlocked: bool


class JourneyStatusResponse(BaseModel):
    session_id: str
    user_role: str
    current_stage: str
    progress: int
    karma: int
    companions: list[str]
    chapter: int
    level_id: int
    knowledge_cards: list[KnowledgeCard]
    achievements: list[Achievement]
    cleared_chapters: list[int]


class ChoiceItem(BaseModel):
    text: str
    karma: int
    success: bool


class JourneyResponse(BaseModel):
    think: str | None = None
    reply: str
    scene_description: str
    stage: str
    choices: list[ChoiceItem]
    progress: int
    karma: int
    chapter: int
    level_id: int
    chapter_name: str
    monster_name: str
    monster_description: str
    knowledge_card: Optional[KnowledgeCard] = None
    achievements: list[Achievement] = []
    examples: list[dict] | None = None
