"""报告相关 Schema——异步报告生成与轮询。"""

from pydantic import BaseModel, Field
from app.agent.schemas.suggestion import AnalysisReport


class GenerateReportRequest(BaseModel):
    class_id: int = Field(..., gt=0)
    class_name: str = Field(default="未知班级")
    exam_ids: list[int] = Field(..., min_length=1)
    modules: list[str] = Field(
        default=["weak-points", "tiered-teaching", "student-lists"],
        description="weak-points, trends, enrollment, tiered-teaching, student-lists"
    )


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # "processing" / "completed" / "failed"
    progress: int
    result: dict | None = None
    created_at: str | None = None
