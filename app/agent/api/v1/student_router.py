"""学生个体查询 API——查看学生画像和知识掌握情况。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.agent.repositories.score_record_repo import ScoreRecordRepo
from app.agent.repositories.student_repo import StudentRepo
from app.agent.repositories.exam_repo import ExamRepo
from app.agent.services.kp_comparison_engine import KPComparisonEngine

router = APIRouter(prefix="/students", tags=["agent-students"])


@router.get("/{student_no}")
def get_student_profile(student_no: str, db: Session = Depends(get_db)):
    """获取学生基本信息和知识掌握概况。"""
    repo = StudentRepo(db)
    student = repo.get_by_no(student_no)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.get("/{student_no}/scores")
def get_student_scores(
    student_no: str,
    exam_id: int = Query(..., description="考试 ID"),
    db: Session = Depends(get_db),
):
    """获取学生在某次考试中各知识点的得分详情。"""
    repo = ScoreRecordRepo(db)
    scores = repo.get_student_kp_scores(student_no, [exam_id])
    return {
        "student_no": student_no,
        "exam_id": exam_id,
        "kp_scores": [
            {
                "kp_id": s["kp_id"],
                "kp_name": s["kp_name"],
                "score_rate": round(s["total_score"] / s["total_max"], 4) if s["total_max"] else 0,
            }
            for s in scores
        ],
    }


@router.get("/{student_no}/trend")
def get_student_trend(
    student_no: str,
    exam_ids: list[int] = Query(..., description="考试 ID 列表"),
    kp_id: int | None = Query(default=None, description="可选: 知识点 ID"),
    db: Session = Depends(get_db),
):
    """获取学生在历次考试中的知识点变化趋势。"""
    engine = KPComparisonEngine(db)
    result = engine.get_student_trend(
        student_no=student_no,
        exam_ids=exam_ids,
        kp_id=kp_id,
    )
    return result


@router.get("/class/{class_id}")
def get_class_students(class_id: int, db: Session = Depends(get_db)):
    """获取某班级所有学生列表。"""
    repo = StudentRepo(db)
    students = repo.get_by_class(class_id)
    return {"class_id": class_id, "students": students, "count": len(students)}
