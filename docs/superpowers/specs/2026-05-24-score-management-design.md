# 成绩考核管理模块设计

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现成绩考核管理模块，支持成绩录入、查询、修改、删除。

**Architecture:** 采用 FastAPI 分层架构（API → Service → Repository → Model），与其他模块（Student、Teacher、Class）保持一致的代码组织模式。

**Tech Stack:** FastAPI + SQLAlchemy + Pydantic v2 + MySQL

---

## 1. 数据模型

### Score 表（scores）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| student_no | VARCHAR(20) | 学号，外键关联 students 表 |
| student_name | VARCHAR(100) | 学生姓名（冗余字段，录入时从 students 表复制） |
| exam_name | VARCHAR(100) | 考试名称（自定义，不限制） |
| score | DECIMAL(5,2) | 成绩（>= 0） |
| is_deleted | BOOL | 逻辑删除标记，默认 False |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 建表 SQL

```sql
CREATE TABLE scores (
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

---

## 2. API 端点

### 成绩路由：/api/v1/scores

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /scores | 获取成绩列表（支持筛选） |
| POST | /scores | 录入成绩 |
| GET | /scores/{id} | 获取成绩详情 |
| PUT | /scores/{id} | 修改成绩 |
| DELETE | /scores/{id} | 逻辑删除成绩 |

---

## 3. Schema 定义

### ScoreCreate（录入）
- student_no: str（必填，关联验证）
- exam_name: str（必填）
- score: float（必填，>= 0）

### ScoreUpdate（更新）
- exam_name: str（可选）
- score: float（可选，>= 0）

### ScoreDetail（详情）
- id: int
- student_no: str
- student_name: str
- exam_name: str
- score: float
- created_at: datetime
- updated_at: datetime

### PaginatedScores
- items: list[ScoreDetail]
- total: int

---

## 4. 业务规则

1. **学号验证**：录入/更新成绩时，学号必须关联已存在的、未删除的学生
2. **姓名自动填充**：录入时从 students 表复制学生姓名到冗余字段
3. **成绩范围**：score >= 0（不设上限）
4. **考试名称**：自定义输入，不做限制
5. **逻辑删除**：DELETE 操作设置 is_deleted = True，不物理删除

---

## 5. 筛选逻辑

GET /scores 支持以下筛选参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| student_no | str | 学号精确匹配 |
| exam_name | str | 考试名称模糊匹配 |
| student_name | str | 学生姓名模糊匹配 |

模糊匹配使用 SQL LIKE，需对特殊字符（%、_）进行转义处理。

---

## 6. 文件结构

- `app/models/score_model.py` — Score ORM 模型
- `app/schemas/score_schema.py` — ScoreCreate, ScoreUpdate, ScoreDetail, PaginatedScores
- `app/repositories/score_repository.py` — ScoreRepository（CRUD + 模糊搜索）
- `app/repositories/student_repository.py` — 现有 StudentRepository 需新增 get_by_student_no_with_deleted 方法（include_deleted=True）
- `app/services/score_service.py` — ScoreService（业务逻辑）
- `app/api/v1/score_router.py` — 成绩路由
- `app/main.py` — 注册 score_router
- `scripts/create_tables.sql` — 添加 scores 表

---

## 7. 错误处理

| 场景 | HTTP 状态码 | 错误信息 |
|------|-------------|----------|
| 学号不存在或已删除 | 400 | 学生 {student_no} 不存在 |
| 成绩 ID 不存在 | 404 | 成绩 {id} 不存在 |
| 成绩 < 0 | 400 | 成绩不能为负数 |