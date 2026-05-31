import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.novels import NovelsChatRequest
from app.services.novels_unified import NovelsUnifiedService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/novels", tags=["Novels"])


@router.post("/chat")
async def chat(request: NovelsChatRequest, db: Session = Depends(get_db)):
    """Unified Four Great Novels chat endpoint - SSE streaming"""
    service = NovelsUnifiedService(db)

    def generate():
        try:
            for chunk in service.chat_stream(request.session_id, request.message, request.model):
                yield chunk
        except Exception as e:
            logger.error(f"[NovelsAPI] Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
