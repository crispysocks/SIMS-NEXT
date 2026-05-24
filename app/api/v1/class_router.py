from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.class_service import ClassService
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassDetail, PaginatedClasses

router = APIRouter(prefix="/classes", tags=["classes"])


def get_class_service(db: Session = Depends(get_db)) -> ClassService:
    return ClassService(db)


@router.get("", response_model=PaginatedClasses)
def list_classes(
    class_no: Optional[str] = Query(None, description="班级编号筛选（模糊匹配）"),
    class_name: Optional[str] = Query(None, description="班级名称筛选（模糊匹配）"),
    service: ClassService = Depends(get_class_service)
):
    return service.list_classes(class_no, class_name)


@router.post("", response_model=ClassDetail, status_code=201)
def create_class(
    data: ClassCreate,
    service: ClassService = Depends(get_class_service)
):
    try:
        return service.create_class(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{class_id}", response_model=ClassDetail)
def get_class(
    class_id: int,
    service: ClassService = Depends(get_class_service)
):
    try:
        return service.get_class(class_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"班级 {class_id} 不存在")


@router.put("/{class_id}", response_model=ClassDetail)
def update_class(
    class_id: int,
    data: ClassUpdate,
    service: ClassService = Depends(get_class_service)
):
    try:
        return service.update_class(class_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{class_id}", status_code=204)
def delete_class(
    class_id: int,
    service: ClassService = Depends(get_class_service)
):
    try:
        service.delete_class(class_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"班级 {class_id} 不存在")