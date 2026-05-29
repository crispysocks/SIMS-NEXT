"""对话 API Router —— POST 提交消息 + GET SSE 流式 + 会话管理。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.agent.core.session_manager import SessionManager, session_manager
from app.agent.core.agent_loop import run_agent_loop

router = APIRouter(prefix="/chat", tags=["agent-chat"])


class CreateSessionRequest(BaseModel):
    user_id: int = Field(..., description="用户 ID")
    class_id: int = Field(..., description="班级 ID")
    class_name: str = Field(default="未知班级", description="班级名称（用于 System Prompt）")
    title: str = Field(default="新对话", description="会话标题")


class SendMessageRequest(BaseModel):
    session_id: str = Field(..., description="会话 UUID")
    text: str = Field(..., min_length=1, max_length=2000, description="用户消息")


# ── Session CRUD ────────────────────────────────

@router.post("/sessions", status_code=201)
def create_session(req: CreateSessionRequest, db: Session = Depends(get_db)):
    sm = SessionManager(db)
    session = sm.create_session(
        user_id=req.user_id,
        class_id=req.class_id,
        title=req.title,
    )
    return {"session_id": session.id, "title": session.title, "class_id": session.class_id}


@router.get("/sessions")
def list_sessions(
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    sm = SessionManager(db)
    sessions = sm.list_sessions(user_id)
    return [
        {
            "id": s.id,
            "title": s.title,
            "class_id": s.class_id,
            "status": s.status,
            "message_count": len(sm.get_messages(s.id)),
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    sm = SessionManager(db)
    session = sm.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = sm.get_all_messages(session_id)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content_json": m.content_json,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/sessions/{session_id}/archive", status_code=204)
def archive_session(session_id: str, db: Session = Depends(get_db)):
    sm = SessionManager(db)
    sm.archive_session(session_id)


# ── Chat Stream ─────────────────────────────────

@router.post("/message")
def send_message(req: SendMessageRequest):
    """提交用户消息，返回 stream_id 用于 SSE 连接。"""
    stream_id = session_manager.create_stream(req.session_id, req.text)
    return {"stream_id": stream_id, "session_id": req.session_id}


@router.get("/stream/{stream_id}")
async def stream_chat(stream_id: str, db: Session = Depends(get_db)):
    """SSE 流式端点——前端用 EventSource 连接此 URL。"""
    data = session_manager.get_stream(stream_id)
    if not data:
        raise HTTPException(status_code=404, detail="stream_id 无效或已过期")

    session_id = data["session_id"]
    user_message = data["user_message"]

    sm = SessionManager(db)
    session = sm.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    async def event_generator():
        async for sse_str in run_agent_loop(
            db=db,
            sm=sm,
            session_id=session_id,
            user_message=user_message,
            class_id=session.class_id,
            class_name=session.title or f"班级{session.class_id}",
        ):
            yield sse_str

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Data Fetch ──────────────────────────────────

@router.get("/data/{data_id}")
def get_analysis_data(data_id: str, db: Session = Depends(get_db)):
    """根据 data_id 获取完整分析数据（用于大数据卡片按需加载）。"""
    sm = SessionManager(db)
    ad = sm.get_analysis_data(data_id)
    if not ad:
        raise HTTPException(status_code=404, detail="数据不存在或已过期")
    return {"data_id": ad.id, "tool_name": ad.tool_name, "data": ad.data_json}
