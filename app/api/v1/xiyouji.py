from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.xiyouji import (
    ChatRequest,
    ChatResponse,
    JourneyStartRequest,
    JourneyChoiceRequest,
    JourneyStatusResponse,
    JourneyResponse,
)
from app.services.xiyouji_service import XiyoujiService
from app.services.xiyouji_journey_service import XiyoujiJourneyService

router = APIRouter(prefix="/xiyouji", tags=["唐僧Agent"])


def get_xiyouji_service(db: Session = Depends(get_db)) -> XiyoujiService:
    return XiyoujiService(db)


def get_journey_service(db: Session = Depends(get_db)) -> XiyoujiJourneyService:
    return XiyoujiJourneyService(db)


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


@router.post("/journey/start", response_model=JourneyResponse)
def journey_start(
    request: JourneyStartRequest, service: XiyoujiJourneyService = Depends(get_journey_service)
):
    """
    开始取经游戏。

    - **session_id**: 会话 ID
    """
    result = service.start_journey(request.session_id)
    return result


@router.post("/journey/choice", response_model=JourneyResponse)
def journey_choice(
    request: JourneyChoiceRequest, service: XiyoujiJourneyService = Depends(get_journey_service)
):
    """
    用户做出选择，推进剧情。

    - **session_id**: 会话 ID
    - **choice**: 用户选择的描述
    """
    result = service.handle_choice(request.session_id, request.choice)
    return result


@router.get("/journey/status", response_model=JourneyStatusResponse)
def journey_status(
    session_id: str, service: XiyoujiJourneyService = Depends(get_journey_service)
):
    """
    查看当前取经状态。

    - **session_id**: 会话 ID
    """
    journey = service.repo.get_active_journey(session_id)
    if not journey:
        return JourneyStatusResponse(
            session_id=session_id,
            user_role="无",
            current_stage="未开始",
            progress=0,
            karma=0,
            companions=[],
            chapter=0,
            level_id=0,
            knowledge_cards=[],
            achievements=[],
            cleared_chapters=[],
        )
    return JourneyStatusResponse(
        session_id=journey.session_id,
        user_role=journey.user_role,
        current_stage=journey.current_stage or "未开始",
        progress=journey.progress,
        karma=journey.karma,
        companions=journey.companions or [],
        chapter=journey.chapter,
        level_id=journey.level_id,
        knowledge_cards=journey.knowledge_cards or [],
        achievements=journey.achievements or [],
        cleared_chapters=journey.cleared_chapters or [],
    )