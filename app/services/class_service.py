from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.class_repository import ClassRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.student_repository import StudentRepository
from app.models.class_model import Class
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassDetail, PaginatedClasses


class ClassService:
    def __init__(self, db: Session):
        self.repo = ClassRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.student_repo = StudentRepository(db)

    def create_class(self, data: ClassCreate) -> ClassDetail:
        if self.repo.exists_by_class_no(data.class_no):
            raise ValueError(f"班级编号 {data.class_no} 已存在")

        if not self.teacher_repo.get_by_teacher_no(data.head_teacher_no):
            raise ValueError(f"教师 {data.head_teacher_no} 不存在")

        if self.repo.exists_by_head_teacher_no(data.head_teacher_no):
            raise ValueError(f"教师 {data.head_teacher_no} 已担任其他班级班主任")

        class_obj = Class(
            class_no=data.class_no,
            class_name=data.class_name,
            head_teacher_no=data.head_teacher_no,
        )
        created = self.repo.create(class_obj)
        return ClassDetail.model_validate(created)

    def get_class(self, class_id: int) -> ClassDetail:
        class_obj = self.repo.get_by_id(class_id)
        if not class_obj:
            raise ValueError(f"班级 {class_id} 不存在")
        return ClassDetail.model_validate(class_obj)

    def list_classes(
        self,
        class_no: Optional[str] = None,
        class_name: Optional[str] = None
    ) -> PaginatedClasses:
        classes = self.repo.list(class_no, class_name)
        return PaginatedClasses(
            items=[ClassDetail.model_validate(c) for c in classes],
            total=len(classes)
        )

    def update_class(self, class_id: int, data: ClassUpdate) -> ClassDetail:
        class_obj = self.repo.get_by_id(class_id)
        if not class_obj:
            raise ValueError(f"班级 {class_id} 不存在")

        if data.head_teacher_no and data.head_teacher_no != class_obj.head_teacher_no:
            if not self.teacher_repo.get_by_teacher_no(data.head_teacher_no):
                raise ValueError(f"教师 {data.head_teacher_no} 不存在")
            if self.repo.exists_by_head_teacher_no(data.head_teacher_no, exclude_id=class_id):
                raise ValueError(f"教师 {data.head_teacher_no} 已担任其他班级班主任")

        if data.class_no and data.class_no != class_obj.class_no:
            if self.repo.exists_by_class_no(data.class_no, exclude_id=class_id):
                raise ValueError(f"班级编号 {data.class_no} 已存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(class_obj, key, value)

        updated = self.repo.update(class_obj)
        return ClassDetail.model_validate(updated)

    def delete_class(self, class_id: int) -> None:
        class_obj = self.repo.get_by_id(class_id)
        if not class_obj:
            raise ValueError(f"班级 {class_id} 不存在")

        self.student_repo.clear_class_for_students(class_obj.id)
        self.repo.soft_delete(class_obj)