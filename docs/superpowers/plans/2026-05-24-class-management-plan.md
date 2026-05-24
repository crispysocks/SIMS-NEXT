# 班级管理模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现班级管理模块的 CRUD 功能，支持模糊搜索和班主任唯一性校验

**Architecture:** 沿用现有分层架构（API → Service → Repository → Model），与学生/教师模块保持一致

**Tech Stack:** FastAPI + SQLAlchemy + Pydantic v2 + MySQL

---

## 文件结构

```
app/
├── models/
│   └── class.py              # Class ORM 模型（新增）
├── schemas/
│   └── class.py             # ClassCreate, ClassUpdate, ClassDetail, PaginatedClasses（新增）
├── repositories/
│   └── class_repository.py  # 数据访问层（新增）
├── services/
│   └── class_service.py      # 业务逻辑层（新增）
└── api/v1/
    └── class.py              # API 路由（新增）

scripts/
└── create_tables.sql         # 修改：添加 classes 表

app/models/__init__.py        # 修改：导出 Class
app/schemas/__init__.py       # 修改：导出 class schemas
app/repositories/__init__.py  # 修改：导出 ClassRepository
app/services/__init__.py      # 修改：导出 ClassService
app/main.py                   # 修改：注册 class router
```

---

## Task 1: 创建 Class 模型

**Files:**
- Create: `app/models/class.py`
- Modify: `app/models/__init__.py`

- [ ] **Step 1: 创建 Class 模型**

```python
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Index
from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_no = Column(String(50), unique=True, nullable=False, index=True)
    class_name = Column(String(100), nullable=False)
    head_teacher_no = Column(String(20), unique=True, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_class_no_deleted", "class_no", "is_deleted"),
        Index("idx_head_teacher_no_deleted", "head_teacher_no", "is_deleted"),
    )
```

- [ ] **Step 2: 更新 models/__init__.py**

```python
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.class import Class

__all__ = ["Student", "Teacher", "Class"]
```

- [ ] **Step 3: 提交**

```bash
git add app/models/class.py app/models/__init__.py
git commit -m "feat: add Class model"
```

---

## Task 2: 创建 Class Pydantic Schemas

**Files:**
- Create: `app/schemas/class.py`
- Modify: `app/schemas/__init__.py`

- [ ] **Step 1: 创建 schemas/class.py**

```python
from datetime import date, datetime
from pydantic import BaseModel, Field


class ClassBase(BaseModel):
    class_no: str = Field(..., min_length=1, max_length=50, description="班级编号")
    class_name: str = Field(..., min_length=1, max_length=100, description="班级名称")
    head_teacher_no: str = Field(..., min_length=6, max_length=20, description="班主任工号")


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    class_no: Optional[str] = Field(None, min_length=1, max_length=50)
    class_name: Optional[str] = Field(None, min_length=1, max_length=100)
    head_teacher_no: Optional[str] = Field(None, min_length=6, max_length=20)


class ClassDetail(ClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedClasses(BaseModel):
    items: list[ClassDetail]
    total: int
```

- [ ] **Step 2: 更新 schemas/__init__.py**

```python
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentDetail,
    PaginatedStudents,
)
from app.schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherDetail,
    PaginatedTeachers,
)
from app.schemas.class import (
    ClassCreate,
    ClassUpdate,
    ClassDetail,
    PaginatedClasses,
)

__all__ = [
    "StudentCreate",
    "StudentUpdate",
    "StudentDetail",
    "PaginatedStudents",
    "TeacherCreate",
    "TeacherUpdate",
    "TeacherDetail",
    "PaginatedTeachers",
    "ClassCreate",
    "ClassUpdate",
    "ClassDetail",
    "PaginatedClasses",
]
```

- [ ] **Step 3: 提交**

```bash
git add app/schemas/class.py app/schemas/__init__.py
git commit -m "feat: add Class schemas"
```

---

## Task 3: 创建 ClassRepository

**Files:**
- Create: `app/repositories/class_repository.py`
- Modify: `app/repositories/__init__.py`

- [ ] **Step 1: 创建 repositories/class_repository.py**

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.class import Class


class ClassRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Class]:
        query = self.db.query(Class).filter(Class.id == id)
        if not include_deleted:
            query = query.filter(Class.is_deleted == False)
        return query.first()

    def get_by_class_no(self, class_no: str, include_deleted: bool = False) -> Optional[Class]:
        query = self.db.query(Class).filter(Class.class_no == class_no)
        if not include_deleted:
            query = query.filter(Class.is_deleted == False)
        return query.first()

    def exists_by_class_no(self, class_no: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Class.id).filter(
            and_(
                Class.class_no == class_no,
                Class.is_deleted == False
            )
        )
        if exclude_id:
            query = query.filter(Class.id != exclude_id)
        return query.first() is not None

    def exists_by_head_teacher_no(self, head_teacher_no: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Class.id).filter(
            and_(
                Class.head_teacher_no == head_teacher_no,
                Class.is_deleted == False
            )
        )
        if exclude_id:
            query = query.filter(Class.id != exclude_id)
        return query.first() is not None

    def create(self, class_obj: Class) -> Class:
        self.db.add(class_obj)
        self.db.commit()
        self.db.refresh(class_obj)
        return class_obj

    def update(self, class_obj: Class) -> Class:
        self.db.commit()
        self.db.refresh(class_obj)
        return class_obj

    def soft_delete(self, class_obj: Class) -> None:
        class_obj.is_deleted = True
        self.db.commit()

    def list(
        self,
        class_no: Optional[str] = None,
        class_name: Optional[str] = None
    ) -> list[Class]:
        query = self.db.query(Class).filter(Class.is_deleted == False)

        if class_no:
            query = query.filter(Class.class_no.like(f"%{class_no}%"))
        if class_name:
            query = query.filter(Class.class_name.like(f"%{class_name}%"))

        return query.all()
```

- [ ] **Step 2: 更新 repositories/__init__.py**

```python
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.class_repository import ClassRepository

__all__ = ["StudentRepository", "TeacherRepository", "ClassRepository"]
```

- [ ] **Step 3: 提交**

```bash
git add app/repositories/class_repository.py app/repositories/__init__.py
git commit -m "feat: add ClassRepository"
```

---

## Task 4: 创建 ClassService

**Files:**
- Create: `app/services/class_service.py`
- Modify: `app/services/__init__.py`
- Modify: `app/repositories/student_repository.py` (添加 clear_class_for_students 方法)

- [ ] **Step 1: 创建 services/class_service.py**

```python
from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.class_repository import ClassRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.student_repository import StudentRepository
from app.models.class import Class
from app.schemas.class import ClassCreate, ClassUpdate, ClassDetail, PaginatedClasses


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

        self.student_repo.clear_class_for_students(class_obj.class_no)
        self.repo.soft_delete(class_obj)
```

- [ ] **Step 2: 在 StudentRepository 中添加 clear_class_for_students 方法**

在 `app/repositories/student_repository.py` 的 `StudentRepository` 类中添加:

```python
def clear_class_for_students(self, class_no: str) -> int:
    """清空属于指定班级的学生的班级信息"""
    from app.models.student import Student
    result = self.db.query(Student).filter(
        and_(
            Student.class_no == class_no,
            Student.is_deleted == False
        )
    ).update({"class_no": None})
    self.db.commit()
    return result
```

- [ ] **Step 3: 更新 services/__init__.py**

```python
from app.services.student_service import StudentService
from app.services.teacher_service import TeacherService
from app.services.class_service import ClassService

__all__ = ["StudentService", "TeacherService", "ClassService"]
```

- [ ] **Step 4: 提交**

```bash
git add app/services/class_service.py app/services/__init__.py app/repositories/student_repository.py
git commit -m "feat: add ClassService"
```

---

## Task 5: 创建 API 路由

**Files:**
- Create: `app/api/v1/class.py`
- Modify: `app/main.py`

- [ ] **Step 1: 创建 api/v1/class.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.class_service import ClassService
from app.schemas.class import ClassCreate, ClassUpdate, ClassDetail, PaginatedClasses

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
```

- [ ] **Step 2: 更新 main.py**

```python
from fastapi import FastAPI
from app.api.v1.student import router as student_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.class import router as class_router

app = FastAPI(title="SIMS-NEXT", description="Student Information Management System")

app.include_router(student_router, prefix="/api/v1")
app.include_router(teacher_router, prefix="/api/v1")
app.include_router(class_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 3: 提交**

```bash
git add app/api/v1/class.py app/main.py
git commit -m "feat: add class API routes"
```

---

## Task 6: 更新数据库脚本

**Files:**
- Modify: `scripts/create_tables.sql`

- [ ] **Step 1: 添加 classes 表**

在 `scripts/create_tables.sql` 末尾添加:

```sql
CREATE TABLE IF NOT EXISTS classes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    class_no VARCHAR(50) NOT NULL UNIQUE,
    class_name VARCHAR(100) NOT NULL,
    head_teacher_no VARCHAR(20) NOT NULL UNIQUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_class_no_deleted (class_no, is_deleted),
    INDEX idx_head_teacher_no_deleted (head_teacher_no, is_deleted)
);
```

- [ ] **Step 2: 提交**

```bash
git add scripts/create_tables.sql
git commit -m "feat: add classes table to database script"
```

---

## Task 7: 最终验证

- [ ] **Step 1: 启动服务器验证**

```bash
uv run fastapi dev app/main.py --port 51888
```

- [ ] **Step 2: 测试 API 端点**

```bash
curl http://localhost:51888/api/v1/classes
curl http://localhost:51888/health
```

- [ ] **Step 3: 提交验证更改**

```bash
git add -A && git commit -m "test: verify class management module"
```