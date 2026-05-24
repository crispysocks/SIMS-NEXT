from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.teacher_service import TeacherService
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherDetail, PaginatedTeachers

router = APIRouter(prefix="/teachers", tags=["teachers"])

def get_teacher_service(db: Session = Depends(get_db)) -> TeacherService:
    return TeacherService(db)

@router.get("", response_model=PaginatedTeachers)
def list_teachers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="姓名筛选（模糊匹配）"),
    teacher_no: Optional[str] = Query(None, description="工号筛选（精确匹配）"),
    service: TeacherService = Depends(get_teacher_service)
):
    return service.list_teachers(page, page_size, name, teacher_no)

@router.post("", response_model=TeacherDetail, status_code=201)
def create_teacher(
    data: TeacherCreate,
    service: TeacherService = Depends(get_teacher_service)
):
    try:
        return service.create_teacher(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{teacher_no}", response_model=TeacherDetail)
def get_teacher(
    teacher_no: str,
    service: TeacherService = Depends(get_teacher_service)
):
    try:
        return service.get_teacher(teacher_no)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"教师 {teacher_no} 不存在")

@router.put("/{teacher_no}", response_model=TeacherDetail)
def update_teacher(
    teacher_no: str,
    data: TeacherUpdate,
    service: TeacherService = Depends(get_teacher_service)
):
    try:
        return service.update_teacher(teacher_no, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{teacher_no}", status_code=204)
def delete_teacher(
    teacher_no: str,
    service: TeacherService = Depends(get_teacher_service)
):
    try:
        service.delete_teacher(teacher_no)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"教师 {teacher_no} 不存在")