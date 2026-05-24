from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.score_service import ScoreService
from app.schemas.score_schema import ScoreCreate, ScoreUpdate, ScoreDetail, PaginatedScores

router = APIRouter(prefix="/scores", tags=["scores"])


def get_score_service(db: Session = Depends(get_db)) -> ScoreService:
    return ScoreService(db)


@router.get("", response_model=PaginatedScores)
def list_scores(
    student_no: Optional[str] = Query(None, description="学号精确匹配"),
    exam_name: Optional[str] = Query(None, description="考试名称筛选（模糊匹配）"),
    student_name: Optional[str] = Query(None, description="学生姓名筛选（模糊匹配）"),
    service: ScoreService = Depends(get_score_service)
):
    return service.list_scores(student_no, exam_name, student_name)


@router.post("", response_model=ScoreDetail, status_code=201)
def create_score(
    data: ScoreCreate,
    service: ScoreService = Depends(get_score_service)
):
    try:
        return service.create_score(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{score_id}", response_model=ScoreDetail)
def get_score(
    score_id: int,
    service: ScoreService = Depends(get_score_service)
):
    try:
        return service.get_score(score_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"成绩 {score_id} 不存在")


@router.put("/{score_id}", response_model=ScoreDetail)
def update_score(
    score_id: int,
    data: ScoreUpdate,
    service: ScoreService = Depends(get_score_service)
):
    try:
        return service.update_score(score_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{score_id}", status_code=204)
def delete_score(
    score_id: int,
    service: ScoreService = Depends(get_score_service)
):
    try:
        service.delete_score(score_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"成绩 {score_id} 不存在")