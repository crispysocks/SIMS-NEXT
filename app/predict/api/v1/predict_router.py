from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.predict.services.prediction_service import PredictionService
from app.predict.services.portrait_service import PortraitService
from app.predict.services.risk_service import RiskService
from app.predict.services.simulation_service import SimulationService
from app.predict.repositories.exam_record_repository import ExamRecordRepository
from app.predict.schemas.prediction import StudentPrediction, WhatIfResult
from app.predict.schemas.portrait import StudentPortraitDetail, RiskWarning

router = APIRouter(prefix="/predict", tags=["升学预测"])


@router.get("/{student_id}/score")
def get_student_avg_score(student_id: int, db: Session = Depends(get_db)):
    """获取学生最近一次考试的总分"""
    exam_repo = ExamRecordRepository(db)
    latest_records = exam_repo.get_latest_by_student(student_id)
    if not latest_records:
        return {"total_score": 0, "count": 0}

    # 只取最近一次考试的科目（按exam_name分组，取最新的考试）
    latest_exam_name = latest_records[0].exam_name
    latest_exam_records = [r for r in latest_records if r.exam_name == latest_exam_name]

    total_score = sum(float(r.score) for r in latest_exam_records)
    return {"total_score": round(total_score, 2), "count": len(latest_exam_records)}


@router.get("/{student_id}", response_model=StudentPrediction)
def get_student_prediction(
    student_id: int,
    current_score: float = Query(..., description="学生当前分数"),
    db: Session = Depends(get_db)
):
    prediction_service = PredictionService(db)
    return prediction_service.predict_student_admission(student_id, current_score)


@router.get("/{student_id}/portrait", response_model=StudentPortraitDetail)
def get_student_portrait(student_id: int, db: Session = Depends(get_db)):
    portrait_service = PortraitService(db)
    try:
        result = portrait_service.analyze_student(student_id)
        if not result:
            raise HTTPException(status_code=404, detail="学生画像不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/risk", response_model=RiskWarning)
def get_risk_warning(student_id: int, db: Session = Depends(get_db)):
    risk_service = RiskService(db)
    return risk_service.analyze_risk(student_id)


@router.get("/{student_id}/simulation", response_model=list[WhatIfResult])
def simulate_score_increase(
    student_id: int,
    subject: str = Query("数学", description="科目"),
    db: Session = Depends(get_db)
):
    exam_repo = ExamRecordRepository(db)
    latest_records = exam_repo.get_latest_by_student(student_id)
    if not latest_records:
        raise HTTPException(status_code=404, detail="无考试成绩数据")

    latest_exam_name = latest_records[0].exam_name
    latest_exam_records = [r for r in latest_records if r.exam_name == latest_exam_name]
    current_score = sum(float(r.score) for r in latest_exam_records)

    simulation_service = SimulationService(db)
    return simulation_service.simulate(student_id, current_score, subject)