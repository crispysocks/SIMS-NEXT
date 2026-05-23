from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.student_service import StudentService
from app.schemas.student import StudentCreate, StudentUpdate, StudentDetail, PaginatedStudents

router = APIRouter(prefix="/students", tags=["students"])

def get_student_service(db: Session = Depends(get_db)) -> StudentService:
    return StudentService(db)

@router.get("", response_model=PaginatedStudents)
def list_students(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="姓名筛选（模糊匹配）"),
    student_no: Optional[str] = Query(None, description="学号筛选（精确匹配）"),
    class_id: Optional[int] = Query(None, description="班级筛选"),
    service: StudentService = Depends(get_student_service)
):
    return service.list_students(page, page_size, name, student_no, class_id)

@router.post("", response_model=StudentDetail, status_code=201)
def create_student(
    data: StudentCreate,
    service: StudentService = Depends(get_student_service)
):
    try:
        return service.create_student(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_no}", response_model=StudentDetail)
def get_student(
    student_no: str,
    service: StudentService = Depends(get_student_service)
):
    try:
        return service.get_student(student_no)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"学生 {student_no} 不存在")

@router.put("/{student_no}", response_model=StudentDetail)
def update_student(
    student_no: str,
    data: StudentUpdate,
    service: StudentService = Depends(get_student_service)
):
    try:
        return service.update_student(student_no, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{student_no}", status_code=204)
def delete_student(
    student_no: str,
    service: StudentService = Depends(get_student_service)
):
    try:
        service.delete_student(student_no)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"学生 {student_no} 不存在")