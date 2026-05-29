# SIMS-NEXT 学生信息管理系统

基于 FastAPI 构建的学生信息管理系统，支持学生、教师、班级和成绩的完整 CRUD 操作。

## 1. 项目概述

| 属性 | 值 |
|------|-----|
| 项目名称 | SIMS-NEXT |
| 版本 | 0.1.0 |
| Python 版本 | >= 3.12 |
| 许可证 | MIT |

### 1.1 功能特性

- **学生管理** - 学生信息的增删改查，支持按学号、姓名模糊搜索
- **教师管理** - 教师信息的增删改查，支持按工号、姓名模糊搜索
- **班级管理** - 班级信息的增删改查，班主任唯一约束
- **成绩考核** - 成绩录入与查询，支持按学号、考试名称、学生姓名筛选

## 2. 技术栈

| 技术 | 说明 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy 2.0 | ORM |
| Pydantic v2 | 数据验证 |
| MySQL | 数据库 |
| Uvicorn | ASGI 服务器 |
| uv | 依赖管理 |

## 3. 项目结构

```
SIMS-NEXT/
├── app/
│   ├── api/v1/           # API 路由层
│   │   ├── student.py    # 学生路由
│   │   ├── teacher.py    # 教师路由
│   │   ├── class_router.py   # 班级路由
│   │   └── score_router.py   # 成绩路由
│   ├── core/             # 核心配置
│   │   ├── config.py     # 数据库配置
│   │   └── database.py   # 数据库连接
│   ├── models/           # ORM 模型
│   │   ├── student.py
│   │   ├── teacher.py
│   │   ├── class_model.py
│   │   └── score_model.py
│   ├── repositories/     # 数据访问层
│   │   ├── student_repository.py
│   │   ├── teacher_repository.py
│   │   ├── class_repository.py
│   │   └── score_repository.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── student.py
│   │   ├── teacher.py
│   │   ├── class_schema.py
│   │   └── score_schema.py
│   ├── services/         # 业务逻辑层
│   │   ├── student_service.py
│   │   ├── teacher_service.py
│   │   ├── class_service.py
│   │   └── score_service.py
│   └── main.py           # 应用入口
├── docs/
│   ├── PRD.md           # 需求文档
│   └── PROJECT.md       # 本文档
├── scripts/
│   └── create_tables.sql # 数据库建表脚本
├── pyproject.toml       # 项目配置
├── .env.example         # 环境变量示例
└── README.md            # 快速入门
```

## 4. 核心模块

### 4.1 学生管理 (students)

- **功能**: 学号、姓名、性别、年龄、籍贯、班级、入学时间管理
- **搜索**: 支持按学号(精确)、姓名(模糊)、班级筛选
- **删除**: 逻辑删除 (`is_deleted` 标记)

### 4.2 教师管理 (teachers)

- **功能**: 工号、姓名、性别、入职时间管理
- **搜索**: 支持按工号(精确)、姓名(模糊)筛选
- **删除**: 逻辑删除

### 4.3 班级管理 (classes)

- **功能**: 班级编号、名称、班主任管理
- **约束**: 班主任工号唯一
- **删除**: 逻辑删除

### 4.4 成绩考核 (scores)

- **功能**: 学号、考试名称、成绩录入
- **考试名称**: 月考1-6、期中考试、期末考试
- **搜索**: 支持按学号、考试名称、学生姓名筛选

## 5. 数据库结构

### 5.1 实体关系

```
学生 ────── 属于 ────── 班级
  │
  └─── 参与 ────── 考试 ────── 对应成绩

教师 ────── 担任 ────── 班主任（班级）
```

- 学生与班级：**N:1**（一个学生属于一个班级）
- 成绩与学生：**N:1**（一个学生有多次成绩记录）
- 班级与班主任（教师）：**N:1**

### 5.2 数据表

| 表名 | 说明 |
|------|------|
| students | 学生表 - id, 学号, 姓名, 性别, 年龄, 籍贯, 班级编号, 入学时间, 删除标记, 创建/更新时间 |
| teachers | 教师表 - id, 工号, 姓名, 性别, 入职时间, 删除标记, 创建/更新时间 |
| classes | 班级表 - id, 班级编号, 班级名称, 班主任工号, 删除标记, 创建/更新时间 |
| scores | 成绩表 - id, 学号, 学生姓名, 考试名称, 成绩, 删除标记, 创建/更新时间 |

## 6. API 端点

所有 API 位于 `/api/v1/` 前缀下。

### 6.1 学生管理 `/api/v1/students`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /students | 获取学生列表 (分页、筛选) |
| POST | /students | 创建学生 |
| GET | /students/{student_no} | 获取学生详情 |
| PUT | /students/{student_no} | 更新学生 |
| DELETE | /students/{student_no} | 删除学生 |

### 6.2 教师管理 `/api/v1/teachers`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /teachers | 获取教师列表 |
| POST | /teachers | 创建教师 |
| GET | /teachers/{id} | 获取教师详情 |
| PUT | /teachers/{id} | 更新教师 |
| DELETE | /teachers/{id} | 删除教师 |

### 6.3 班级管理 `/api/v1/classes`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /classes | 获取班级列表 |
| POST | /classes | 创建班级 |
| GET | /classes/{id} | 获取班级详情 |
| PUT | /classes/{id} | 更新班级 |
| DELETE | /classes/{id} | 删除班级 |

### 6.4 成绩考核 `/api/v1/scores`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /scores | 获取成绩列表 |
| POST | /scores | 录入成绩 |
| GET | /scores/{id} | 获取成绩详情 |
| PUT | /scores/{id} | 修改成绩 |
| DELETE | /scores/{id} | 删除成绩 |

## 7. 快速开始

### 7.1 环境要求

- Python 3.12+
- MySQL 5.7+

### 7.2 安装步骤

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写数据库信息

# 3. 初始化数据库
mysql -u root -p -e "source scripts/create_tables.sql"

# 4. 启动服务
uv run uvicorn app.main:app --reload --port 8000
```

### 7.3 API 文档

启动服务后访问: http://localhost:8000/docs (Swagger UI)

## 8. 架构设计

### 8.1 分层架构

```
请求 → Router → Service → Repository → Model → Database
         ↓
       Schema (数据验证)
```

- **Router**: 处理 HTTP 请求/响应，参数验证
- **Service**: 业务逻辑处理，事务管理
- **Repository**: 数据访问封装，查询构建
- **Model**: ORM 模型定义

### 8.2 目录职责

| 目录 | 职责 |
|------|------|
| api/v1/ | API 路由定义 |
| core/ | 核心配置 (数据库、Application) |
| models/ | SQLAlchemy ORM 模型 |
| repositories/ | 数据访问层 |
| schemas/ | Pydantic 数据验证模型 |
| services/ | 业务逻辑层 |

## 9. 开发规范

1. **软删除**: 所有实体使用 `is_deleted` 标记删除状态
2. **模糊搜索**: 使用 SQL `LIKE` 语句，需转义特殊字符
3. **分页**: 默认页大小 20，最大 100
4. **错误处理**: 使用 `ValueError` + HTTP 400/404 异常

### 9.1 添加新模块流程

1. 创建 Model (`app/models/`)
2. 创建 Schema (`app/schemas/`)
3. 创建 Repository (`app/repositories/`)
4. 创建 Service (`app/services/`)
5. 创建 Router (`app/api/v1/`)
6. 在 `main.py` 中注册路由
7. 更新数据库脚本 (`scripts/create_tables.sql`)

## 10. 环境变量

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your-user-name
DB_PASSWORD=your-user-password
DB_NAME=sims
```

## 11. 许可证

MIT License