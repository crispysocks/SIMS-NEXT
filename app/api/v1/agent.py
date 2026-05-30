from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["Agent"])

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    model: str = Field(default="gpt-4o-mini")

@router.post("/chat")
async def chat(request: ChatRequest):
    """流式问答接口"""
    agent = AgentService()

    def generate():
        for chunk in agent.chat_stream(request.question, request.model):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )