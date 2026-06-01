from pydantic import BaseModel, Field


class NovelsChatRequest(BaseModel):
    session_id: str = Field(..., description="Client session ID")
    message: str = Field(..., min_length=1, max_length=2000)
    model: str | None = Field(default=None)


class ChoiceItem(BaseModel):
    text: str
    karma: int
    success: bool


class KnowledgeCard(BaseModel):
    title: str
    content: str


class Achievement(BaseModel):
    id: str
    name: str
    description: str
    unlocked: bool
