"""分析响应 Schema——F1-F5 API 的结构化返回结果。"""

from __future__ import annotations
from pydantic import BaseModel, Field


class KPItem(BaseModel):
    """单个知识点的掌握情况。"""
    kp_id: int
    name: str
    level: int
    parent_id: int | None = None
    mastery_rate: float
    class_avg_score: float
    grade_avg_score: float
    deviation: float
    discrimination: float


class WeakPointResponse(BaseModel):
    class_id: int
    exam_ids: list[int]
    knowledge_points: list[KPItem]
    summary: str = ""


class TierInfo(BaseModel):
    label: str
    rank_range: str
    students: list[dict]
    avg_score: float
    headcount: int


class TierAnalysisResponse(BaseModel):
    class_id: int
    exam_id: int
    tiers: dict[str, TierInfo]
    summary: str = ""


class StudentTrendPoint(BaseModel):
    exam_id: int
    exam_name: str
    score_rate: float
    rank: int | None = None


class StudentTrendResponse(BaseModel):
    student_no: str
    kp_id: int | None = None
    trend: str  # "rising"/"falling"/"volatile"/"stable"
    slope: float
    data_points: list[StudentTrendPoint]


class StudentListItem(BaseModel):
    student_no: str
    name: str = ""
    total_score: float
    weak_kps: list[dict]
    rank: int


class StudentListResponse(BaseModel):
    class_id: int
    exam_id: int
    students: list[StudentListItem]
    common_weak_kps: list[dict]


class TrendSummaryResponse(BaseModel):
    class_id: int
    exam_ids: list[int]
    exam_avgs: list[float]
    slope: float
    direction: str  # "上升"/"下降"/"波动"/"持平"
    weak_kp_trends: list[dict]


class EnrollmentResponse(BaseModel):
    class_id: int
    target_score_line: float
    enrollment_rate: float
    borderline_students: list[dict]
    risk_students: list[dict]
    summary: str = ""


class QuestionQualityItem(BaseModel):
    question_id: int
    title: str
    difficulty: float
    discrimination: float
    quality_label: str  # "优秀"/"一般"/"低质量"


class QuestionQualityResponse(BaseModel):
    exam_id: int
    questions: list[QuestionQualityItem]
    low_quality_count: int


class RankSummaryResponse(BaseModel):
    class_id: int
    exam_id: int
    top_n: int
    avg_score: float
    students: list[dict]
    common_weak_kps: list[dict]
