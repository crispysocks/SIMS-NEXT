# SIMS-NEXT

K12 学生信息管理系统 + AI 教学分析 + 四大名著智能助手。

## 项目组成

| 模块 | 说明 |
|------|------|
| **SIMS 教务管理** | 学生/教师/班级/成绩 CRUD，JWT 认证 |
| **AI 教学分析 Agent** | 学情诊断、知识点薄弱点定位、分层教学建议 |
| **四大名著助手** | 基于 PageIndex + Milvus 的 RAG 问答 + 西游记取经文字游戏 |

## 技术栈

**后端:** FastAPI · SQLAlchemy · MySQL · OpenAI SDK · PageIndex · Milvus · PyJWT

**前端:** React 18 · Vite · TypeScript · Tailwind CSS 4 · Shadcn/ui · Zustand

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 5.7+
- Milvus（可选，用于四大名著语义检索）

### 启动

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 初始化数据库
mysql -u root -p -e "source scripts/create_tables.sql"

# 3. 启动后端
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 4. 启动前端（另开终端）
cd frontend && npm install && npm run dev
```

前端 http://localhost:3000  
API 文档 http://localhost:8000/docs

## 项目结构

```
SIMS-NEXT/
├── app/
│   ├── api/v1/              # REST API 路由
│   │   ├── auth.py          # 认证
│   │   ├── student.py       # 学生
│   │   ├── teacher.py       # 教师
│   │   ├── class_router.py  # 班级
│   │   ├── score_router.py  # 成绩
│   │   └── novels.py        # 四大名著助手
│   ├── agent/               # AI 教学分析 Agent 子系统
│   │   ├── api/v1/          # Agent API
│   │   ├── core/            # Agent loop, LLM client, prompts
│   │   ├── models/          # 知识点/考试/分析数据模型
│   │   ├── services/        # 分析引擎（趋势/分层/薄弱点等）
│   │   └── tools/           # Agent 工具定义
│   ├── core/
│   │   ├── config.py        # 全局配置（环境变量驱动）
│   │   ├── database.py      # 数据库连接池
│   │   ├── embedding.py     # Embedding API 客户端
│   │   ├── logging_config.py
│   │   ├── milvus.py        # Milvus 向量检索
│   │   └── pageindex/       # PageIndex 文档索引
│   ├── models/              # SIMS ORM 模型
│   ├── repositories/        # 数据访问层
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── services/            # 业务逻辑层
│   │   ├── novels_unified.py  # 四大名著统一 Agent
│   │   ├── journey_engine.py  # 西游记游戏状态机
│   │   └── rag_service.py     # PageIndex 检索封装
│   ├── config/
│   │   └── journey_chapters.py  # 游戏关卡配置
│   └── main.py              # 应用入口
├── frontend/src/
│   ├── pages/               # 页面组件
│   │   ├── NovelsChat.tsx   # 四大名著统一聊天页
│   │   └── Chat.tsx         # AI 助教聊天页
│   ├── stores/              # Zustand 状态管理
│   ├── components/ui/       # Shadcn/ui 组件
│   └── lib/                 # API 封装 & 工具函数
├── scripts/                 # 索引构建脚本 & SQL
├── workspace/novels/        # PageIndex 索引文件
├── docs/                    # PRD & 技术文档
└── pyproject.toml
```

## API 概览

### 认证 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/register | 注册 |
| POST | /auth/login | 登录 |

### 教务管理 `/api/v1`

| 资源 | 端点 | 操作 |
|------|------|------|
| Students | /students | CRUD + 分页搜索 |
| Teachers | /teachers | CRUD + 分页搜索 |
| Classes | /classes | CRUD + 分页搜索 |
| Scores | /scores | CRUD + 多条件筛选 |

### 四大名著助手 `/api/v1/novels`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /novels/chat | 统一对话接口（SSE 流式） |

支持通用四大名著问答和西游记取经文字游戏，LLM 自动判断意图路由。

### AI 教学分析 Agent `/api/v1/agent`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /agent/chat | 教学分析对话（SSE 流式） |
| POST | /agent/analysis | 学情分析 |
| POST | /agent/report | 教学报告 |
| GET | /agent/students | 班级学生列表 |

## 环境变量

完整配置见 `.env.example`。

### 数据库

| 变量 | 默认值 |
|------|--------|
| DB_HOST | localhost |
| DB_PORT | 3306 |
| DB_USER / DB_PASSWORD | user / password |
| DB_NAME | sims |

### LLM

| 变量 | 默认值 |
|------|--------|
| LLM_BASE_URL | https://api.deepseek.com/v1 |
| LLM_API_KEY | — |
| LLM_MODEL | deepseek-chat |

### 检索

| 变量 | 默认值 | 说明 |
|------|--------|------|
| MILVUS_HOST | localhost | Milvus 向量数据库 |
| MILVUS_PORT | 19530 | |
| MILVUS_COLLECTION | xiyouji | 集合名称 |
| EMBED_MODEL | text-embedding-3-small | Embedding 模型 |
