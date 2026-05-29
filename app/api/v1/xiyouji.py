from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.xiyouji import ChatRequest, ChatResponse
from app.services.xiyouji_service import XiyoujiService

router = APIRouter(prefix="/xiyouji", tags=["唐僧Agent"])


def get_xiyouji_service(db: Session = Depends(get_db)) -> XiyoujiService:
    return XiyoujiService(db)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, service: XiyoujiService = Depends(get_xiyouji_service)):
    """
    发送消息给唐僧，获取回复。

    - **session_id**: 会话 ID，用于关联对话历史
    - **message**: 用户消息
    - **history**: 可选的历史对话列表（如果传入则优先使用服务端存储的历史）
    """
    result = service.chat(request.session_id, request.message, request.history)
    return ChatResponse(**result)