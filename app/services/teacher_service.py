from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.teacher_repository import TeacherRepository
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherDetail, PaginatedTeachers


class TeacherService:
    def __init__(self, db: Session):
        self.repo = TeacherRepository(db)

    def create_teacher(self, data: TeacherCreate) -> TeacherDetail:
        if self.repo.exists_by_teacher_no(data.teacher_no):
            raise ValueError(f"工号 {data.teacher_no} 已存在")

        teacher = Teacher(
            teacher_no=data.teacher_no,
            name=data.name,
            gender=data.gender,
            entry_date=data.entry_date,
        )
        created = self.repo.create(teacher)
        return TeacherDetail.model_validate(created)

    def get_teacher(self, teacher_no: str) -> TeacherDetail:
        teacher = self.repo.get_by_teacher_no(teacher_no)
        if not teacher:
            raise ValueError(f"教师 {teacher_no} 不存在")
        return TeacherDetail.model_validate(teacher)

    def list_teachers(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        teacher_no: Optional[str] = None
    ) -> PaginatedTeachers:
        skip = (page - 1) * page_size
        teachers, total = self.repo.list(skip, page_size, name, teacher_no)
        return PaginatedTeachers(
            items=[TeacherDetail.model_validate(t) for t in teachers],
            total=total,
            page=page,
            page_size=page_size
        )

    def update_teacher(self, teacher_no: str, data: TeacherUpdate) -> TeacherDetail:
        teacher = self.repo.get_by_teacher_no(teacher_no)
        if not teacher:
            raise ValueError(f"教师 {teacher_no} 不存在")

        if data.teacher_no and data.teacher_no != teacher_no:
            if self.repo.exists_by_teacher_no(data.teacher_no, exclude_id=teacher.id):
                raise ValueError(f"工号 {data.teacher_no} 已存在")
            teacher.teacher_no = data.teacher_no

        update_data = data.model_dump(exclude_unset=True, exclude={"teacher_no"})
        for key, value in update_data.items():
            if value is not None:
                setattr(teacher, key, value)

        updated = self.repo.update(teacher)
        return TeacherDetail.model_validate(updated)

    def delete_teacher(self, teacher_no: str) -> None:
        teacher = self.repo.get_by_teacher_no(teacher_no)
        if not teacher:
            raise ValueError(f"教师 {teacher_no} 不存在")
        self.repo.soft_delete(teacher)