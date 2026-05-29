# SIMS-NEXT 智能教育平台

基于 FastAPI + React 构建的 K12 学校学生信息管理系统，支持学生、教师、班级和成绩的完整 CRUD 操作。

## 功能特性

- **用户认证** - JWT token 登录注册，支持用户管理
- **学生管理** - 学生信息的增删改查，支持按学号、姓名搜索
- **教师管理** - 教师信息的增删改查，支持按工号、姓名搜索
- **班级管理** - 班级信息的增删改查，班主任唯一约束
- **成绩考核** - 成绩录入与查询，支持按学号、考试名称、学生姓名筛选

## 技术栈

### 后端

| 技术 | 说明 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy | ORM |
| Pydantic v2 | 数据验证 |
| MySQL | 数据库 |
| PyJWT | JWT 认证 |
| bcrypt | 密码加密 |
| uv | 依赖管理 |

### 前端

| 技术 | 说明 |
|------|------|
| React 18 + Vite | 框架与构建 |
| TypeScript | 类型系统 |
| Tailwind CSS 4 | 样式框架 |
| Shadcn/ui | UI 组件库 |
| zustand | 状态管理 |
| react-router-dom v6 | 路由管理 |

## 项目结构

```
SIMS-NEXT/
├── app/                      # 后端应用
│   ├── api/v1/              # API 路由层
│   │   ├── auth.py          # 认证路由
│   │   ├── student.py       # 学生路由
│   │   ├── teacher.py       # 教师路由
│   │   ├── class_router.py  # 班级路由
│   │   └── score_router.py  # 成绩路由
│   ├── core/                # 核心配置
│   │   ├── config.py        # 应用配置
│   │   └── database.py      # 数据库连接
│   ├── models/              # ORM 模型
│   │   ├── user.py         # 用户模型
│   │   ├── student.py
│   │   ├── teacher.py
│   │   ├── class_model.py
│   │   └── score_model.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── auth.py          # 认证 Schema
│   │   ├── student.py
│   │   ├── teacher.py
│   │   ├── class_schema.py
│   │   └── score_schema.py
│   ├── services/            # 业务逻辑层
│   │   ├── auth_service.py  # 认证服务
│   │   ├── student_service.py
│   │   ├── teacher_service.py
│   │   ├── class_service.py
│   │   └── score_service.py
│   └── main.py              # 应用入口
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── components/      # React 组件
│   │   │   ├── ui/          # Shadcn/ui 组件
│   │   │   └── Layout/      # 布局组件
│   │   ├── pages/           # 页面组件
│   │   │   ├── Login.tsx
│   │   │   ├── Students.tsx
│   │   │   ├── Teachers.tsx
│   │   │   ├── Classes.tsx
│   │   │   └── Scores.tsx
│   │   ├── stores/          # zustand 状态管理
│   │   │   ├── authStore.ts
│   │   │   ├── studentStore.ts
│   │   │   ├── teacherStore.ts
│   │   │   ├── classStore.ts
│   │   │   └── scoreStore.ts
│   │   ├── lib/             # 工具函数
│   │   │   ├── api.ts       # API 封装
│   │   │   └── utils.ts
│   │   ├── App.tsx          # 路由配置
│   │   └── main.tsx        # 入口文件
│   ├── components.json      # Shadcn/ui 配置
│   └── package.json
├── docs/                    # 文档
│   ├── PRD.md              # 需求文档
│   └── superpowers/        # 开发规范文档
├── scripts/
│   └── create_tables.sql   # 数据库建表脚本
├── pyproject.toml          # 后端项目配置
├── .env.example           # 环境变量示例
└── README.md
```

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 5.7+

### 1. 启动后端

```bash
# 安装后端依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 修改数据库连接配置

# 初始化数据库
mysql -u root -p -e "source scripts/create_tables.sql"

# 启动后端服务
uv run uvicorn app.main:app --reload --port 8000
```

### 2. 启动前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问 http://localhost:3000

后端 API 文档 http://localhost:8000/docs

## API 文档

### 认证 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/register | 用户注册 |
| POST | /auth/login | 用户登录 |

### 学生管理 `/api/v1/students`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /students | 获取学生列表（分页、筛选） |
| POST | /students | 创建学生 |
| GET | /students/{student_no} | 获取学生详情 |
| PUT | /students/{student_no} | 更新学生 |
| DELETE | /students/{student_no} | 删除学生 |

### 教师管理 `/api/v1/teachers`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /teachers | 获取教师列表（分页、筛选） |
| POST | /teachers | 创建教师 |
| GET | /teachers/{teacher_no} | 获取教师详情 |
| PUT | /teachers/{teacher_no} | 更新教师 |
| DELETE | /teachers/{teacher_no} | 删除教师 |

### 班级管理 `/api/v1/classes`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /classes | 获取班级列表（分页、筛选） |
| POST | /classes | 创建班级 |
| GET | /classes/{class_id} | 获取班级详情 |
| PUT | /classes/{class_id} | 更新班级 |
| DELETE | /classes/{class_id} | 删除班级 |

### 成绩考核 `/api/v1/scores`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /scores | 获取成绩列表（分页、筛选） |
| POST | /scores | 录入成绩 |
| GET | /scores/{score_id} | 获取成绩详情 |
| PUT | /scores/{score_id} | 修改成绩 |
| DELETE | /scores/{score_id} | 删除成绩 |

## 开发指南

### 后端添加新模块

1. 创建 Model (`app/models/`)
2. 创建 Schema (`app/schemas/`)
3. 创建 Service (`app/services/`)
4. 创建 Router (`app/api/v1/`)
5. 在 `main.py` 中注册路由
6. 更新数据库脚本 (`scripts/create_tables.sql`)

### 前端添加新模块

1. 创建 zustand store (`frontend/src/stores/`)
2. 创建页面组件 (`frontend/src/pages/`)
3. 在 `App.tsx` 中添加路由

### 代码规范

- 使用软删除模式 (`is_deleted` 标记)
- 模糊搜索需使用 `_escape_like` 转义特殊字符
- 遵循分层架构: API → Service → Repository → Model
- 前端使用 zustand 管理状态，fetch 封装 API 调用

# 配置说明

项目支持通过 `.env` 文件配置以下参数：

### 数据库配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_HOST` | localhost | 数据库主机 |
| `DB_PORT` | 3306 | 数据库端口 |
| `DB_USER` | user | 数据库用户名 |
| `DB_PASSWORD` | password | 数据库密码 |
| `DB_NAME` | sims | 数据库名称 |

### JWT 认证配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `JWT_SECRET_KEY` | sims-next-secret-key-change-in-production | 令牌签名密钥 |
| `JWT_EXPIRE_MINUTES` | 1440 | Token 有效期（分钟） |

### 数据库连接池配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_POOL_SIZE` | 5 | 连接池大小 |
| `DB_MAX_OVERFLOW` | 10 | 最大溢出连接数 |

### API 路由配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `API_PREFIX` | /api/v1 | API 路由前缀 |

### 前端配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `VITE_API_BASE_URL` | /api/v1 | 前端 API 请求基础路径 |

## 许可证

MIT License