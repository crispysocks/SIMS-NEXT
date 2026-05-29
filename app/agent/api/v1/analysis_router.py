"""分析 API Router —— F1-F5 端点，所有接口返回结构化 JSON 数据。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.agent.schemas.analysis_request import (
    WeakPointRequest,
    TierAnalysisRequest,
    StudentTrendRequest,
    StudentListRequest,
    TrendRequest,
    EnrollmentRequest,
    QuestionQualityRequest,
    RankSummaryRequest,
)
from app.agent.schemas.analysis_response import (
    WeakPointResponse,
    TierAnalysisResponse,
    StudentTrendResponse,
    StudentListResponse,
    TrendSummaryResponse,
    EnrollmentResponse,
    QuestionQualityResponse,
    RankSummaryResponse,
)
from app.agent.services.weak_point_engine import WeakPointEngine
from app.agent.services.tier_engine import TierEngine
from app.agent.services.student_list_engine import StudentListEngine
from app.agent.services.trend_engine import TrendEngine
from app.agent.services.enrollment_engine import EnrollmentEngine
from app.agent.services.question_quality import QuestionQualityService
from app.agent.services.kp_comparison_engine import KPComparisonEngine
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.repositories.knowledge_point_repo import KnowledgePointRepo
from app.agent.repositories.exam_repo import ExamRepo

router = APIRouter(prefix="/analysis", tags=["agent-analysis"])


# ── F1: 薄弱知识点分析 ──────────────────────────

@router.post("/weak-points", response_model=WeakPointResponse)
def analyze_weak_points(req: WeakPointRequest, db: Session = Depends(get_db)):
    engine = WeakPointEngine(db)
    result = engine.analyze(
        class_id=req.class_id,
        exam_ids=req.exam_ids,
        kp_ids=req.kp_ids,
    )
    return result


# ── F4: 分层教学 ────────────────────────────────

@router.post("/tiers", response_model=TierAnalysisResponse)
def analyze_tiers(req: TierAnalysisRequest, db: Session = Depends(get_db)):
    engine = TierEngine(db)
    result = engine.analyze(class_id=req.class_id, exam_id=req.exam_id)
    return result


# ── F5: 培优名单 ────────────────────────────────

@router.post("/student-lists/advanced", response_model=StudentListResponse)
def get_advanced_list(req: StudentListRequest, db: Session = Depends(get_db)):
    engine = StudentListEngine(db)
    result = engine.get_advanced(class_id=req.class_id, exam_id=req.exam_id)
    return result


@router.post("/student-lists/remedial", response_model=StudentListResponse)
def get_remedial_list(req: StudentListRequest, db: Session = Depends(get_db)):
    engine = StudentListEngine(db)
    result = engine.get_remedial(class_id=req.class_id, exam_id=req.exam_id)
    return result


# ── F2: 趋势分析 ────────────────────────────────

@router.post("/trends", response_model=TrendSummaryResponse)
def analyze_trends(req: TrendRequest, db: Session = Depends(get_db)):
    engine = TrendEngine(db)
    result = engine.analyze(class_id=req.class_id, exam_ids=req.exam_ids)
    return result


@router.post("/student-trend", response_model=StudentTrendResponse)
def get_student_trend(req: StudentTrendRequest, db: Session = Depends(get_db)):
    engine = KPComparisonEngine(db)
    result = engine.get_student_trend(
        student_no=req.student_no,
        exam_ids=req.exam_ids,
        kp_id=req.kp_id,
    )
    return result


# ── F3: 升学分析 ────────────────────────────────

@router.post("/enrollment", response_model=EnrollmentResponse)
def analyze_enrollment(req: EnrollmentRequest, db: Session = Depends(get_db)):
    engine = EnrollmentEngine(db)
    result = engine.analyze(
        class_id=req.class_id,
        target_score_line=req.target_score_line,
    )
    return result


# ── 题目质量分析 ────────────────────────────────

@router.post("/question-quality", response_model=QuestionQualityResponse)
def analyze_question_quality(req: QuestionQualityRequest, db: Session = Depends(get_db)):
    service = QuestionQualityService(db)
    result = service.analyze(
        exam_id=req.exam_id,
        question_ids=req.question_ids,
    )
    return result


# ── 排名汇总 ─────────────────────────────────────

@router.post("/rank-summary", response_model=RankSummaryResponse)
def get_rank_summary(req: RankSummaryRequest, db: Session = Depends(get_db)):
    repo = ScoreRecordRepo(db)
    result = repo.get_top_students_summary(
        class_id=req.class_id,
        exam_id=req.exam_id,
        top_n=req.top_n,
    )
    return result


# ── 知识点依赖查询 ──────────────────────────────

@router.get("/dependencies/{kp_id}")
def get_kp_dependencies(kp_id: int, db: Session = Depends(get_db)):
    repo = KnowledgePointRepo(db)
    deps = repo.get_dependencies(kp_id)
    chain = repo.get_dependency_chain(kp_id)
    return {"kp_id": kp_id, "dependencies": deps, "chain": chain}


# ── 知识点树 ─────────────────────────────────────

@router.get("/knowledge-tree/{subject_id}")
def get_knowledge_tree(subject_id: int, db: Session = Depends(get_db)):
    repo = KnowledgePointRepo(db)
    tree = repo.get_tree(subject_id)
    return {"subject_id": subject_id, "tree": tree}


# ── 考试列表 ─────────────────────────────────────

@router.get("/exams/{class_id}")
def get_class_exams(class_id: int, subject_id: int | None = None, db: Session = Depends(get_db)):
    repo = ExamRepo(db)
    exams = repo.get_by_class(class_id, subject_id)
    return {"class_id": class_id, "exams": exams}
