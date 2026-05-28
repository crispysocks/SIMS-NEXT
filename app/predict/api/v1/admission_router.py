from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.predict.services.score_line_service import ScoreLineService
from app.predict.schemas.admission_line import ScoreLinePrediction

router = APIRouter(prefix="/admission-line", tags=["分数线预测"])


@router.get("/{school_id}", response_model=ScoreLinePrediction)
def get_score_line_prediction(
    school_id: int,
    target_year: int = Query(2026, description="目标年份"),
    db: Session = Depends(get_db)
):
    score_line_service = ScoreLineService(db)
    result = score_line_service.predict_score_line(school_id, target_year)
    if not result:
        raise HTTPException(status_code=404, detail="无历史数据")
    return result