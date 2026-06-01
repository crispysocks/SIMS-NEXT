# SIMS-NEXT

K12 学生信息管理系统 + AI 教学分析 + 升学预测 + AI 智能辅导 + 四大名著智能助手。

## 项目组成

| 模块 | 说明 |
|------|------|
| **SIMS 教务管理** | 学生/教师/班级/成绩 CRUD，JWT 认证 |
| **AI 教学分析 Agent** | 学情诊断、知识点薄弱点定位、分层教学建议 |
| **升学预测** | ML 驱动的学生画像、升学概率预测、风险预警、分数提升模拟与 AI 学习建议 |
| **AI 智能辅导** | 基于贝叶斯掌握度追踪的自适应辅导系统，支持数学和英语双学科 |
| **四大名著助手** | 基于 PageIndex + Milvus 的 RAG 问答 + 西游记取经文字游戏 |

## 技术栈

**后端:** FastAPI · SQLAlchemy · MySQL · OpenAI SDK · PageIndex · Milvus · PyJWT · SymPy · scikit-learn · Anthropic SDK

**前端:** React 19 · Vite 8 · TypeScript 6 · Tailwind CSS 4 · Shadcn/ui · Zustand · React Query · Recharts · ECharts（懒加载）

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
mysql -u root -p --default-character-set=utf8mb4 -e "source scripts/create_tables.sql"

# 3. 启动后端
uv sync
uv run uvicorn app.main:app --reload

# 4. 启动前端（另开终端）
cd frontend && npm install && npm run dev
```

前端 http://localhost:3000  
API 文档 http://localhost:8000/docs

### 前端架构

- **双门户路由**：`/student/*`（学生门户）、`/teacher/*`（教师工作台），登录后按角色自动重定向
- **设计系统**：Indigo（#4F46E5）+ Amber（#F59E0B）双主题（亮/暗），CSS 变量令牌在 `shared/design-system/tokens.css`
- **图表策略**：Recharts 同步加载（折线/柱状/雷达/径向仪表） + ECharts 仅 Heatmap 懒加载（按需下载 ~110kB gzipped）
- **错误体系**：3 级 ErrorBoundary（app/page/section），section 级 inline 重试，page 级居中刷新，app 级兜底
- **Loading 体系**：5 类组件（TopLoader/RouteLoader/Skeleton/ButtonSpinner/TableSkeleton）
- **主题持久化**：`localStorage.sims.theme`，`index.html` 内联脚本防 FOUC
- **测试**：Vitest + Testing Library + jsdom（当前 12 个测试覆盖 Theme/ErrorBoundary/RoleGuard）

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
│   │   ├── novels.py        # 四大名著助手
│   │   └── tutor_router.py  # AI 辅导
│   ├── agent/               # AI 教学分析 Agent 子系统
│   │   ├── api/v1/          # Agent API
│   │   ├── core/            # Agent loop, LLM client, prompts
│   │   ├── models/          # 知识点/考试/分析数据模型
│   │   ├── services/        # 分析引擎（趋势/分层/薄弱点等）
│   │   └── tools/           # Agent 工具定义
│   ├── predict/             # 升学预测子系统
│   │   ├── api/v1/          # 预测 API（升学预测/分数线/AI建议）
│   │   ├── ml/              # ML 模型训练与加载
│   │   ├── models/          # 考试/高中/分数线/学生画像 ORM
│   │   ├── repositories/    # 数据访问层
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # 预测/画像/风险/模拟/聊天服务
│   ├── tutor/               # AI 智能辅导引擎
│   │   ├── core/            # 核心抽象层（掌握度、推荐、会话）
│   │   ├── subjects/        # 学科实现（math、english）
│   │   └── rag/             # RAG 检索增强生成管道
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
│   │   ├── rag_service.py     # PageIndex 检索封装
│   │   └── tutor_service.py   # AI 辅导服务
│   ├── config/
│   │   └── journey_chapters.py  # 游戏关卡配置
│   └── main.py              # 应用入口
├── frontend/src/
│   ├── app/                 # 路由 + Providers 装配
│   │   ├── providers.tsx    # QueryClient / Theme / Auth / ErrorBoundary
│   │   └── router.tsx       # createBrowserRouter + 懒加载路由
│   ├── shared/              # 跨门户共享层
│   │   ├── design-system/  # 设计令牌（CSS 变量 / 双主题）
│   │   ├── theme/          # 自研 ThemeProvider（FOUC 防闪烁）
│   │   ├── components/     # ErrorBoundary、Loading、StatCard、DataTable 等
│   │   ├── charts/         # 图表（Recharts 同步 + ECharts 懒加载 Heatmap）
│   │   ├── stores/         # auth-store（Zustand + persist）
│   │   ├── hooks/          # useRoleGuard 等
│   │   ├── api/            # 业务 API 封装
│   │   └── lib/            # 工具函数
│   ├── portals/            # 双门户：auth / student / teacher
│   │   ├── auth/           # 登录 + 角色分流 + RoleGuard
│   │   ├── student/        # 学生门户（顶导 + Dashboard + Tutor + 预测 + 助教）
│   │   └── teacher/        # 教师工作台（侧栏 + 顶栏 + 主题切换 + Dashboard + CRUD + 分析）
│   ├── components/ui/      # Shadcn/ui 原子组件
│   ├── lib/                # API 基础封装 & 工具
│   └── stores/             # 业务数据 Store（学生/教师/班级/成绩等）
├── scripts/                 # 数据库初始化、索引构建 & LLM 工具脚本
├── workspace/novels/        # PageIndex 索引文件
├── docs/                    # PRD、技术文档 & AI 预测模块介绍
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

### 升学预测 `/api/v1`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /predict/{student_id} | 学生升学概率预测（冲刺/稳定/保底） |
| GET | /predict/{student_id}/score | 获取学生最近考试总分 |
| GET | /predict/{student_id}/portrait | 学生画像分析（学习类型/优势/短板） |
| GET | /predict/{student_id}/risk | 风险预警（波动/下滑科目标签） |
| GET | /predict/{student_id}/simulation | 分数提升模拟（What-if 分析） |
| GET | /admission-line/{school_id} | 高中录取分数线趋势预测 |
| GET | /advice/{student_id} | AI 学习建议（分科针对性建议） |
| POST | /advice/{student_id}/chat | 升学规划对话（SSE 流式） |

### AI 智能辅导 `/api/v1/tutor`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /tutor/question | 获取下一道推荐题目 |
| POST | /tutor/answer | 提交答案，获取诊断与反馈 |
| POST | /tutor/hint | 请求渐进式提示（最多 3 级） |
| GET | /tutor/mastery | 获取所有知识点的掌握度状态 |
| GET | /tutor/progress | 获取完整学习进度快照 |
| POST | /tutor/reset | 重置所有掌握度和会话历史 |
| GET | /tutor/subject | 获取当前学科及可选学科列表 |
| POST | /tutor/subject | 切换学科（math / english） |

## 环境变量

完整配置见 `.env.example`。

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_HOST / DB_PORT | localhost / 3306 | 数据库连接 |
| DB_USER / DB_PASSWORD | root / — | 数据库凭据 |
| DB_NAME | sims | 数据库名称 |
| JWT_SECRET_KEY | — | JWT 签名密钥 |
| LLM_BASE_URL | https://api.deepseek.com/v1 | LLM API 地址 |
| LLM_API_KEY | — | API 密钥 |
| LLM_MODEL | deepseek-chat | 模型名称 |
| MILVUS_HOST / PORT | localhost / 19530 | Milvus 向量数据库 |
| EMBED_MODEL | text-embedding-3-small | Embedding 模型 |
| RAG_ENABLED | false | AI 辅导 RAG 管道开关 |
| RAG_RETRIEVER_MODE | hybrid | RAG 检索模式（hybrid / vector / keyword） |
| RAG_EMBEDDING_MODEL | all-MiniLM-L6-v2 | RAG 本地 Embedding 模型 |

## 许可证

MIT License
