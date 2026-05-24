# SIMS-NEXT 学生信息管理系统

基于 FastAPI 构建的学生信息管理系统，支持学生、教师、班级和成绩的 CRUD 操作。

## 功能特性

- **学生管理** - 学生信息的增删改查，支持按学号、姓名模糊搜索
- **教师管理** - 教师信息的增删改查，支持按工号、姓名模糊搜索
- **班级管理** - 班级信息的增删改查，班主任唯一约束
- **成绩考核** - 成绩录入与查询，支持按学号、考试名称、学生姓名筛选

## 技术栈

| 技术 | 说明 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy | ORM |
| Pydantic v2 | 数据验证 |
| MySQL | 数据库 |
| uv | 依赖管理 |

## 项目结构

```
SIMS-NEXT/
├── app/
│   ├── api/v1/           # API 路由层
│   │   ├── student.py    # 学生路由
│   │   ├── teacher.py    # 教师路由
│   │   ├── class_router.py   # 班级路由
│   │   └── score_router.py   # 成绩路由
│   ├── core/             # 核心配置
│   │   ├── config.py     # 应用配置
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
├── docs/                # 文档
│   ├── PRD.md           # 需求文档
│   └── superpowers/      # 开发规范文档
├── scripts/
│   └── create_tables.sql # 数据库建表脚本
├── pyproject.toml       # 项目配置
└── .env.example         # 环境变量示例
```

## 快速开始

### 环境要求

- Python 3.12+
- MySQL 5.7+

### 安装依赖

```bash
uv sync
```

### 配置环境变量

复制 `.env.example` 为 `.env`，修改数据库连接配置：

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/sims
```

### 初始化数据库

```bash
mysql -u root -p sims < scripts/create_tables.sql
```

### 启动服务

```bash
uv run uvicorn app.main:app --reload --port 8000
```

服务启动后访问 http://localhost:8000/docs 查看 API 文档。

## API 文档

启动服务后访问 Swagger UI: http://localhost:8000/docs

### 学生管理 `/api/v1/students`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /students | 获取学生列表 |
| POST | /students | 创建学生 |
| GET | /students/{id} | 获取学生详情 |
| PUT | /students/{id} | 更新学生 |
| DELETE | /students/{id} | 删除学生 |

### 教师管理 `/api/v1/teachers`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /teachers | 获取教师列表 |
| POST | /teachers | 创建教师 |
| GET | /teachers/{id} | 获取教师详情 |
| PUT | /teachers/{id} | 更新教师 |
| DELETE | /teachers/{id} | 删除教师 |

### 班级管理 `/api/v1/classes`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /classes | 获取班级列表 |
| POST | /classes | 创建班级 |
| GET | /classes/{id} | 获取班级详情 |
| PUT | /classes/{id} | 更新班级 |
| DELETE | /classes/{id} | 删除班级 |

### 成绩考核 `/api/v1/scores`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /scores | 获取成绩列表 |
| POST | /scores | 录入成绩 |
| GET | /scores/{id} | 获取成绩详情 |
| PUT | /scores/{id} | 修改成绩 |
| DELETE | /scores/{id} | 删除成绩 |

## 开发指南

### 添加新模块

1. 创建 Model (`app/models/`)
2. 创建 Schema (`app/schemas/`)
3. 创建 Repository (`app/repositories/`)
4. 创建 Service (`app/services/`)
5. 创建 Router (`app/api/v1/`)
6. 在 `main.py` 中注册路由
7. 更新数据库脚本 (`scripts/create_tables.sql`)

### 代码规范

- 使用软删除模式 (`is_deleted` 标记)
- 模糊搜索需使用 `_escape_like` 转义特殊字符
- 遵循分层架构: API → Service → Repository → Model

## 许可证

MIT License