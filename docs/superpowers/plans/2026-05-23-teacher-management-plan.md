# 教师管理模块实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现教师管理模块的完整 CRUD 功能

**Architecture:** 分层架构，API → Service → Repository → Model，各层职责清晰

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, MySQL

---

## 文件结构

```
app/
├── models/teacher.py          # ORM 模型
├── schemas/teacher.py        # Pydantic 模型
├── repositories/teacher_repository.py  # 数据访问层
├── services/teacher_service.py         # 业务逻辑层
├── api/v1/teacher.py         # 路由层
└── main.py                   # 注册路由（修改）

scripts/
└── create_tables.sql        # 更新数据库脚本
```

---

### Task 1: Teacher ORM 模型

**Files:**
- Create: `app/models/teacher.py`
- Modify: `app/models/__init__.py`

- [ ] **Step 1: 创建 ORM 模型**

```python
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Index
from app.core.database import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_no = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    entry_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_teacher_no_deleted", "teacher_no", "is_deleted"),
    )
```

- [ ] **Step 2: 提交**

```bash
git add app/models/teacher.py app/models/__init__.py
git commit -m "feat: add Teacher ORM model"
```

---

### Task 2: Teacher Pydantic Schema

**Files:**
- Create: `app/schemas/teacher.py`
- Modify: `app/schemas/__init__.py`

- [ ] **Step 1: 创建 Pydantic 模型**

```python
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TeacherBase(BaseModel):
    teacher_no: str = Field(..., min_length=6, max_length=20, description="工号，字母开头+数字")
    name: str = Field(..., min_length=2, max_length=20, description="姓名")
    gender: str = Field(..., description="性别")
    entry_date: date = Field(..., description="入职时间")

    @field_validator("teacher_no")
    @classmethod
    def validate_teacher_no(cls, v: str) -> str:
        if not v[0].isalpha():
            raise ValueError("工号必须以字母开头")
        if not v.isalnum():
            raise ValueError("工号只能包含字母和数字")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("男", "女"):
            raise ValueError("性别只能为男或女")
        return v


class TeacherCreate(TeacherBase):
    pass


class TeacherUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=20)
    gender: Optional[str] = None
    entry_date: Optional[date] = None
    teacher_no: Optional[str] = Field(None, min_length=6, max_length=20)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("男", "女"):
            raise ValueError("性别只能为男或女")
        return v

    @field_validator("teacher_no")
    @classmethod
    def validate_teacher_no(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v[0].isalpha():
                raise ValueError("工号必须以字母开头")
            if not v.isalnum():
                raise ValueError("工号只能包含字母和数字")
        return v


class TeacherDetail(TeacherBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedTeachers(BaseModel):
    items: list[TeacherDetail]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 2: 提交**

```bash
git add app/schemas/teacher.py app/schemas/__init__.py
git commit -m "feat: add Teacher Pydantic schemas"
```

---

### Task 3: Teacher Repository

**Files:**
- Create: `app/repositories/teacher_repository.py`
- Modify: `app/repositories/__init__.py`

- [ ] **Step 1: 创建数据访问层**

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.teacher import Teacher


class TeacherRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_teacher_no(self, teacher_no: str, include_deleted: bool = False) -> Optional[Teacher]:
        query = self.db.query(Teacher).filter(Teacher.teacher_no == teacher_no)
        if not include_deleted:
            query = query.filter(Teacher.is_deleted == False)
        return query.first()

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Teacher]:
        query = self.db.query(Teacher).filter(Teacher.id == id)
        if not include_deleted:
            query = query.filter(Teacher.is_deleted == False)
        return query.first()

    def exists_by_teacher_no(self, teacher_no: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Teacher.id).filter(
            and_(
                Teacher.teacher_no == teacher_no,
                Teacher.is_deleted == False
            )
        )
        if exclude_id:
            query = query.filter(Teacher.id != exclude_id)
        return query.first() is not None

    def create(self, teacher: Teacher) -> Teacher:
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def update(self, teacher: Teacher) -> Teacher:
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def soft_delete(self, teacher: Teacher) -> None:
        teacher.is_deleted = True
        self.db.commit()

    def list(
        self,
        skip: int,
        limit: int,
        name: Optional[str] = None,
        teacher_no: Optional[str] = None
    ) -> tuple[list[Teacher], int]:
        query = self.db.query(Teacher).filter(Teacher.is_deleted == False)

        if name:
            query = query.filter(Teacher.name.like(f"%{name}%"))
        if teacher_no:
            query = query.filter(Teacher.teacher_no == teacher_no)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
```

- [ ] **Step 2: 提交**

```bash
git add app/repositories/teacher_repository.py app/repositories/__init__.py
git commit -m "feat: add TeacherRepository data access layer"
```

---

### Task 4: Teacher Service

**Files:**
- Create: `app/services/teacher_service.py`
- Modify: `app/services/__init__.py`

- [ ] **Step 1: 创建业务逻辑层**

```python
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
```

- [ ] **Step 2: 提交**

```bash
git add app/services/teacher_service.py app/services/__init__.py
git commit -m "feat: add TeacherService business logic layer"
```

---

### Task 5: Teacher API 路由

**Files:**
- Create: `app/api/v1/teacher.py`
- Modify: `app/api/v1/__init__.py`

- [ ] **Step 1: 创建路由**

```python
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
```

- [ ] **Step 2: 提交**

```bash
git add app/api/v1/teacher.py app/api/v1/__init__.py
git commit -m "feat: add Teacher API routes"
```

---

### Task 6: 注册路由到 main.py

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: 添加路由注册**

```python
from fastapi import FastAPI
from app.api.v1.student import router as student_router
from app.api.v1.teacher import router as teacher_router

app = FastAPI(title="SIMS-NEXT API")

app.include_router(student_router, prefix="/api/v1")
app.include_router(teacher_router, prefix="/api/v1")
```

- [ ] **Step 2: 验证应用加载**

```bash
uv run python -c "from app.main import app; print('App loaded OK')"
```

- [ ] **Step 3: 提交**

```bash
git add app/main.py
git commit -m "feat: register teacher router in main.py"
```

---

### Task 7: 更新数据库脚本

**Files:**
- Modify: `scripts/create_tables.sql`

- [ ] **Step 1: 添加教师表**

```sql
CREATE TABLE IF NOT EXISTS teachers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    entry_date DATE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_teacher_no_deleted (teacher_no, is_deleted),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

- [ ] **Step 2: 提交**

```bash
git add scripts/create_tables.sql
git commit -m "feat: add teachers table to database script"
```

---

### Task 8: 验证测试

- [ ] **Step 1: 验证应用加载**

```bash
uv run python -c "from app.main import app; print('All routes:', [r.path for r in app.routes])"
```

- [ ] **Step 2: 验证无语法错误**

```bash
uv run python -c "from app.models.teacher import Teacher; from app.schemas.teacher import TeacherCreate; from app.services.teacher_service import TeacherService; from app.repositories.teacher_repository import TeacherRepository; print('All imports OK')"
```

---

## 自检清单

1. **Spec 覆盖检查**：
   - [ ] 教师表结构与 spec 一致
   - [ ] API 端点与 spec 一致
   - [ ] 字段校验规则与 spec 一致
   - [ ] 工号格式与学生模块一致

2. **占位符扫描**：无 TBD/TODO/未填写内容

3. **类型一致性**：
   - [ ] Teacher 模型字段名与 Schema 一致
   - [ ] Repository 方法签名正确
   - [ ] Service 方法签名正确

---