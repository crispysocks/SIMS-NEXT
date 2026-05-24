# Score Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现成绩考核管理模块，支持成绩录入、查询、修改、删除。

**Architecture:** 采用 FastAPI 分层架构（API → Service → Repository → Model），与其他模块（Student、Teacher、Class）保持一致的代码组织模式。

**Tech Stack:** FastAPI + SQLAlchemy + Pydantic v2 + MySQL

---

## 文件结构

- `app/models/score_model.py` — Score ORM 模型
- `app/schemas/score_schema.py` — ScoreCreate, ScoreUpdate, ScoreDetail, PaginatedScores
- `app/repositories/score_repository.py` — ScoreRepository（CRUD + 模糊搜索）
- `app/services/score_service.py` — ScoreService（业务逻辑）
- `app/api/v1/score_router.py` — 成绩路由
- `app/main.py` — 注册 score_router
- `scripts/create_tables.sql` — 添加 scores 表
- `app/schemas/__init__.py` — 导出 score schemas

---

### Task 1: 创建 Score 数据模型

**Files:**
- Create: `app/models/score_model.py`

- [ ] **Step 1: 创建模型文件**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Index
from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_no = Column(String(20), nullable=False, index=True)
    student_name = Column(String(100), nullable=False)
    exam_name = Column(String(100), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_student_no_deleted", "student_no", "is_deleted"),
        Index("idx_exam_name_deleted", "exam_name", "is_deleted"),
    )
```

- [ ] **Step 2: 提交**

```bash
git add app/models/score_model.py
git commit -m "feat: add Score ORM model"
```

---

### Task 2: 创建 Score Schema

**Files:**
- Create: `app/schemas/score_schema.py`

- [ ] **Step 1: 创建 Schema 文件**

```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ScoreCreate(BaseModel):
    student_no: str = Field(..., min_length=1, max_length=20, description="学号")
    exam_name: str = Field(..., min_length=1, max_length=100, description="考试名称")
    score: float = Field(..., ge=0, description="成绩（>=0）")


class ScoreUpdate(BaseModel):
    exam_name: Optional[str] = Field(None, min_length=1, max_length=100)
    score: Optional[float] = Field(None, ge=0)


class ScoreDetail(BaseModel):
    id: int
    student_no: str
    student_name: str
    exam_name: str
    score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedScores(BaseModel):
    items: list[ScoreDetail]
    total: int
```

- [ ] **Step 2: 提交**

```bash
git add app/schemas/score_schema.py
git commit -m "feat: add Score Pydantic schemas"
```

---

### Task 3: 更新 schemas/__init__.py

**Files:**
- Modify: `app/schemas/__init__.py`

- [ ] **Step 1: 添加 Score 导出**

在文件末尾添加：

```python
from app.schemas.score_schema import (
    ScoreCreate,
    ScoreUpdate,
    ScoreDetail,
    PaginatedScores,
)
```

在 `__all__` 列表中添加：

```python
    "ScoreCreate",
    "ScoreUpdate",
    "ScoreDetail",
    "PaginatedScores",
```

- [ ] **Step 2: 提交**

```bash
git add app/schemas/__init__.py
git commit -m "feat: export Score schemas from __init__"
```

---

### Task 4: 创建 Score Repository

**Files:**
- Create: `app/repositories/score_repository.py`

- [ ] **Step 1: 创建 Repository**

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.score_model import Score


def _escape_like(s: str) -> str:
    """Escape special characters for SQL LIKE patterns"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ScoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Score]:
        query = self.db.query(Score).filter(Score.id == id)
        if not include_deleted:
            query = query.filter(Score.is_deleted == False)
        return query.first()

    def create(self, score_obj: Score) -> Score:
        self.db.add(score_obj)
        self.db.commit()
        self.db.refresh(score_obj)
        return score_obj

    def update(self, score_obj: Score) -> Score:
        self.db.commit()
        self.db.refresh(score_obj)
        return score_obj

    def soft_delete(self, score_obj: Score) -> None:
        score_obj.is_deleted = True
        self.db.commit()

    def list(
        self,
        student_no: Optional[str] = None,
        exam_name: Optional[str] = None,
        student_name: Optional[str] = None
    ) -> list[Score]:
        query = self.db.query(Score).filter(Score.is_deleted == False)

        if student_no:
            query = query.filter(Score.student_no == student_no)
        if exam_name:
            query = query.filter(Score.exam_name.like(f"%{_escape_like(exam_name)}%", escape="\\"))
        if student_name:
            query = query.filter(Score.student_name.like(f"%{_escape_like(student_name)}%", escape="\\"))

        return query.all()
```

- [ ] **Step 2: 提交**

```bash
git add app/repositories/score_repository.py
git commit -m "feat: add ScoreRepository with fuzzy search"
```

---

### Task 5: 创建 Score Service

**Files:**
- Create: `app/services/score_service.py`

- [ ] **Step 1: 创建 Service**

```python
from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.score_repository import ScoreRepository
from app.repositories.student_repository import StudentRepository
from app.models.score_model import Score
from app.schemas.score_schema import ScoreCreate, ScoreUpdate, ScoreDetail, PaginatedScores


class ScoreService:
    def __init__(self, db: Session):
        self.repo = ScoreRepository(db)
        self.student_repo = StudentRepository(db)

    def create_score(self, data: ScoreCreate) -> ScoreDetail:
        student = self.student_repo.get_by_student_no(data.student_no)
        if not student:
            raise ValueError(f"学生 {data.student_no} 不存在")

        score_obj = Score(
            student_no=data.student_no,
            student_name=student.name,
            exam_name=data.exam_name,
            score=data.score,
        )
        created = self.repo.create(score_obj)
        return ScoreDetail.model_validate(created)

    def get_score(self, score_id: int) -> ScoreDetail:
        score_obj = self.repo.get_by_id(score_id)
        if not score_obj:
            raise ValueError(f"成绩 {score_id} 不存在")
        return ScoreDetail.model_validate(score_obj)

    def list_scores(
        self,
        student_no: Optional[str] = None,
        exam_name: Optional[str] = None,
        student_name: Optional[str] = None
    ) -> PaginatedScores:
        scores = self.repo.list(student_no, exam_name, student_name)
        return PaginatedScores(
            items=[ScoreDetail.model_validate(s) for s in scores],
            total=len(scores)
        )

    def update_score(self, score_id: int, data: ScoreUpdate) -> ScoreDetail:
        score_obj = self.repo.get_by_id(score_id)
        if not score_obj:
            raise ValueError(f"成绩 {score_id} 不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(score_obj, key, value)

        updated = self.repo.update(score_obj)
        return ScoreDetail.model_validate(updated)

    def delete_score(self, score_id: int) -> None:
        score_obj = self.repo.get_by_id(score_id)
        if not score_obj:
            raise ValueError(f"成绩 {score_id} 不存在")

        self.repo.soft_delete(score_obj)
```

- [ ] **Step 2: 提交**

```bash
git add app/services/score_service.py
git commit -m "feat: add ScoreService with business logic"
```

---

### Task 6: 创建 Score Router

**Files:**
- Create: `app/api/v1/score_router.py`

- [ ] **Step 1: 创建 Router**

```python
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
```

- [ ] **Step 2: 提交**

```bash
git add app/api/v1/score_router.py
git commit -m "feat: add Score API routes"
```

---

### Task 7: 更新 main.py 注册 Router

**Files:**
- Modify: `app/main.py:1-11`

- [ ] **Step 1: 添加 score_router 导入和注册**

在 import 语句中添加：
```python
from app.api.v1.score_router import router as score_router
```

在 app.include_router 语句中添加：
```python
app.include_router(score_router, prefix="/api/v1")
```

- [ ] **Step 2: 提交**

```bash
git add app/main.py
git commit -m "feat: register score router in main.py"
```

---

### Task 8: 更新 create_tables.sql

**Files:**
- Modify: `scripts/create_tables.sql`

- [ ] **Step 1: 添加 scores 表**

在文件末尾添加：

```sql
CREATE TABLE IF NOT EXISTS scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_no VARCHAR(20) NOT NULL COMMENT '学号',
    student_name VARCHAR(100) NOT NULL COMMENT '学生姓名（冗余）',
    exam_name VARCHAR(100) NOT NULL COMMENT '考试名称',
    score DECIMAL(5,2) NOT NULL COMMENT '成绩（>=0）',
    is_deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_student_no (student_no),
    INDEX idx_exam_name (exam_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

- [ ] **Step 2: 提交**

```bash
git add scripts/create_tables.sql
git commit -m "feat: add scores table to database script"
```

---

## 自检清单

**1. Spec 覆盖检查：**
- [x] Score 数据模型
- [x] ScoreCreate, ScoreUpdate, ScoreDetail, PaginatedScores schemas
- [x] ScoreRepository with CRUD + 模糊搜索
- [x] ScoreService with 学号验证 + 业务逻辑
- [x] Score Router (GET/POST/GET/{id}/PUT/{id}/DELETE/{id})
- [x] main.py 注册
- [x] create_tables.sql 添加 scores 表

**2. 占位符扫描：** 无 TBD/TODO/不完整步骤

**3. 类型一致性：** 检查确认 schema 字段名与 service/repository 一致