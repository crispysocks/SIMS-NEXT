"""异步报告 API —— POST 提交报告任务 + GET 轮询结果。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.agent.services.report_service import submit_report_task, get_task_status

router = APIRouter(prefix="/reports", tags=["agent-reports"])


class GenerateReportRequest(BaseModel):
    class_id: int = Field(..., description="班级 ID")
    class_name: str = Field(default="未知班级")
    exam_ids: list[int] = Field(..., min_length=1, description="考试 ID 列表")
    modules: list[str] = Field(
        default=["weak-points", "tiered-teaching", "student-lists"],
        description="启用的分析模块: weak-points, trends, enrollment, tiered-teaching, student-lists"
    )


@router.post("/generate", status_code=202)
async def generate_report(req: GenerateReportRequest, db: Session = Depends(get_db)):
    """提交综合报告生成任务，返回 task_id 用于轮询。"""
    task_id = await submit_report_task(
        db=db,
        class_id=req.class_id,
        class_name=req.class_name,
        exam_ids=req.exam_ids,
        modules=req.modules,
    )
    return {"task_id": task_id, "status": "processing"}


@router.get("/{task_id}")
def get_report(task_id: str):
    """轮询报告任务状态。"""
    status = get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return {
        "task_id": task_id,
        "status": status["status"],
        "progress": status["progress"],
        "result": status.get("result"),
        "created_at": status.get("created_at"),
    }
