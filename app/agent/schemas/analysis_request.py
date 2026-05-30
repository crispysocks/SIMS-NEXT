"""分析请求 Schema——F1-F5 API 的请求参数校验。"""

from pydantic import BaseModel, Field


class WeakPointRequest(BaseModel):
    class_id: int = Field(..., gt=0, description="班级 ID")
    exam_ids: list[int] = Field(..., min_length=1, description="考试 ID 列表")
    kp_ids: list[int] | None = Field(default=None, description="可选: 限定知识点范围")


class TierAnalysisRequest(BaseModel):
    class_id: int = Field(..., gt=0)
    exam_id: int = Field(..., gt=0)


class StudentTrendRequest(BaseModel):
    student_no: str = Field(..., min_length=1)
    exam_ids: list[int] = Field(..., min_length=1)
    kp_id: int | None = Field(default=None, description="可选: 限定知识点")


class StudentListRequest(BaseModel):
    class_id: int = Field(..., gt=0)
    exam_id: int = Field(..., gt=0)


class TrendRequest(BaseModel):
    class_id: int = Field(..., gt=0)
    exam_ids: list[int] = Field(..., min_length=2)


class EnrollmentRequest(BaseModel):
    class_id: int = Field(..., gt=0)
    target_score_line: float = Field(default=65, ge=0, le=100)


class QuestionQualityRequest(BaseModel):
    exam_id: int = Field(..., gt=0)
    question_ids: list[int] | None = None


class RankSummaryRequest(BaseModel):
    class_id: int = Field(..., gt=0)
    exam_id: int = Field(..., gt=0)
    top_n: int = Field(default=10, ge=1, le=50)
