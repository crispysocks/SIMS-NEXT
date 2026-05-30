"""学生个体查询 API——查看学生画像和知识掌握情况。"""

from collections import defaultdict
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

    score_repo = ScoreRecordRepo(db)
    exam_repo = ExamRepo(db)

    # 获取该学生的班级和所有考试
    class_id = student.get("class_id")
    exams = exam_repo.get_by_class(class_id) if class_id else []

    # 聚合所有考试的知识点得分
    kp_totals: dict[int, dict] = defaultdict(lambda: {"score": 0.0, "max": 0.0, "name": ""})
    exam_performance = []

    for exam in exams:
        exam_id = exam["id"]
        kp_scores = score_repo.get_student_kp_scores(student_no, [exam_id])
        if not kp_scores:
            continue

        exam_total = sum(float(s["total_score"]) for s in kp_scores)
        exam_max = sum(float(s["total_max"]) for s in kp_scores)
        exam_performance.append({
            "exam_id": exam_id,
            "exam_name": exam["name"],
            "exam_date": str(exam.get("exam_date", "")),
            "total_score": round(exam_total, 1),
            "total_max": round(exam_max, 1),
            "score_rate": round(exam_total / exam_max, 4) if exam_max else 0,
        })

        for s in kp_scores:
            kp_id = s["kp_id"]
            kp_totals[kp_id]["score"] += float(s["total_score"])
            kp_totals[kp_id]["max"] += float(s["total_max"])
            kp_totals[kp_id]["name"] = s["kp_name"]

    # 按掌握率分类知识点
    kp_mastery = []
    for kp_id, data in kp_totals.items():
        rate = data["score"] / data["max"] if data["max"] else 0
        kp_mastery.append({
            "kp_id": kp_id,
            "kp_name": data["name"],
            "score_rate": round(rate, 4),
        })

    kp_mastery.sort(key=lambda x: x["score_rate"])

    weak_kps = [k for k in kp_mastery if k["score_rate"] < 0.60]
    strong_kps = [k for k in kp_mastery if k["score_rate"] >= 0.80]

    # 整体掌握率
    overall_score = sum(d["score"] for d in kp_totals.values())
    overall_max = sum(d["max"] for d in kp_totals.values())
    overall_rate = round(overall_score / overall_max, 4) if overall_max else 0

    return {
        **student,
        "overall_mastery_rate": overall_rate,
        "exam_performance": exam_performance[-6:],  # 最近 6 场考试
        "weak_kps": weak_kps,
        "strong_kps": strong_kps,
        "total_kps_analyzed": len(kp_mastery),
    }


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
