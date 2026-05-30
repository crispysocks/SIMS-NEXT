# 班级教学优化 Agent — 技术架构与开发流程

## 1. 总体架构

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI 应用                      │
│                                                     │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │  现有 SIMS 模块   │  │  agent/（新增，独立模块） │ │
│  │  students/       │  │                          │ │
│  │  teachers/       │  │  models/    ORM 模型     │ │
│  │  classes/        │  │  schemas/   Pydantic    │ │
│  │  scores/         │  │  repositories/ 数据访问  │ │
│  └──────────────────┘  │  services/  分析引擎     │ │
│                         │  api/v1/    Router      │ │
│                         │  core/     指标+配置    │ │
│                         │  mock/     Mock 生成    │ │
│                         └──────────────────────────┘ │
│                                                     │
│  共享层：core/database.py（SQLAlchemy Session）       │
│         core/config.py（环境变量）                    │
└─────────────────────────────────────────────────────┘
```

**原则**：
- agent 模块复用现有 `core/database.py` 的数据库连接和 Session 管理
- agent 模块复用现有 `core/config.py` 的环境变量加载
- 不修改现有 SIMS 的任何代码文件
- agent 模块通过 `main.py` 注册新 router，不影响现有路由

---

## 2. 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| Web 框架 | FastAPI（复用） | 新增 agent router |
| ORM | SQLAlchemy（复用） | 声明式模型，复用 Base |
| 数据校验 | Pydantic v2 | 请求/响应 Schema + LLM 输出校验 |
| 数据库 | MySQL（复用） | 新增 agent 专用表 |
| 分析计算 | SQL + Pandas | SQL 做聚合过滤，Pandas 做统计（回归/方差/std） |
| LLM 客户端 | `openai` 包 | 兼容 OpenAI / 国产模型 API |
| 异步 | `asyncio` + 轮询 | POST 提交任务 → GET 轮询结果 |
| Mock 数据 | Faker + 自定义引擎 | 学生画像驱动生成 |
| 规则配置 | JSON 文件 | `app/agent/core/config/tier_rules.json`，启动时加载 |

### 2.1 为什么 SQL + Pandas 混合

| 计算类型 | 放哪里 | 原因 |
|---------|--------|------|
| 按班级/考试/知识点聚合得分 | SQL (GROUP BY + AVG) | 数据量大时数据库引擎更高效 |
| 排名、排序、Top N | SQL (ORDER BY + LIMIT) | 避免全量加载到内存 |
| 线性回归（成长率 slope） | Pandas / scipy | SQL 不适合做回归 |
| 标准差、波动率 | Pandas | SQL std 可用但 Pandas 更灵活 |
| 异常值检测、分布分析 | Pandas | 需要向量化操作 |

### 2.2 异步方案：轮询

```
POST /api/v1/agent/reports/generate
  → 返回 { task_id: "uuid" }（立即返回，不阻塞）
  → 后台 asyncio.create_task() 执行分析+LLM调用
  → 结果写入内存 dict 或临时表

GET /api/v1/agent/reports/{task_id}
  → processing → 返回进度百分比
  → completed → 返回完整报告
  → failed → 返回错误信息
```

MVP 阶段用内存 dict 存储任务状态，后续可换 Redis。

---

## 3. 项目文件结构

```
app/
├── agent/                          # 新增：agent 模块根目录
│   ├── __init__.py
│   │
│   ├── models/                     # ORM 模型
│   │   ├── __init__.py
│   │   ├── subject.py              # Subject
│   │   ├── knowledge_point.py      # KnowledgePoint
│   │   ├── knowledge_dependency.py # KnowledgeDependency
│   │   ├── question.py             # Question
│   │   ├── question_kp.py          # QuestionKnowledgePoint
│   │   ├── exam.py                 # Exam
│   │   └── score_record.py         # ScoreRecord
│   │
│   ├── schemas/                    # Pydantic 请求/响应
│   │   ├── __init__.py
│   │   ├── analysis_request.py     # 分析请求 Schema
│   │   ├── analysis_response.py    # 分析响应 Schema
│   │   ├── report.py               # 报告相关 Schema
│   │   └── suggestion.py           # SuggestionItem（LLM 输出校验）
│   │
│   ├── repositories/               # 数据访问层
│   │   ├── __init__.py
│   │   ├── score_record_repo.py    # ScoreRecord 查询（聚合/分组/排名）
│   │   ├── knowledge_point_repo.py # 知识点树查询 + 依赖 DAG 查询
│   │   ├── exam_repo.py
│   │   └── student_repo.py         # 复用现有 Student 模型做查询
│   │
│   ├── services/                   # 分析引擎（核心）
│   │   ├── __init__.py
│   │   ├── question_quality.py     # 题目质量分析（区分度/难度系数）
│   │   ├── weak_point_engine.py    # F1: 薄弱知识点分析
│   │   ├── trend_engine.py         # F2: 趋势分析
│   │   ├── enrollment_engine.py    # F3: 升学分析
│   │   ├── tier_engine.py          # F4: 分层教学
│   │   ├── student_list_engine.py  # F5: 培优补差名单
│   │   ├── kp_comparison_engine.py # 知识点跨考试对比
│   │   └── report_service.py       # F6: 综合报告生成（含 LLM 调用）
│   │
│   ├── api/                        # API 路由
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── analysis_router.py  # 分析接口（F1-F5）
│   │       ├── report_router.py    # 报告接口（异步）
│   │       ├── student_router.py   # 学生个体查询
│   │       └── mock_router.py      # Mock 数据管理
│   │
│   ├── core/                       # Agent 核心配置
│   │   ├── __init__.py
│   │   ├── metrics.py              # 统一定义的指标体系函数
│   │   └── config/
│   │       ├── __init__.py
│   │       └── tier_rules.json     # 规则配置（阈值/比例/分数线）
│   │
│   └── mock/                       # Mock 数据
│       ├── __init__.py
│       ├── student_profile.py      # 学生画像参数生成
│       ├── score_generator.py      # 基于画像的成绩生成
│       ├── knowledge_tree.py       # 知识点树+依赖+题目 Mock
│       └── cli.py                  # CLI 入口：python -m app.agent.mock
│
├── core/
│   ├── database.py                 # 不改动，复用
│   └── config.py                   # 不改动，复用
│
├── models/                         # 不改动，复用现有
├── repositories/                   # 不改动，复用现有
├── services/                       # 不改动，复用现有
├── api/                            # 不改动，复用现有
│
└── main.py                         # 仅新增一行 router 注册
```

### 3.1 main.py 改动（唯一需要修改的现有文件）

```python
# 新增
from app.agent.api.v1.analysis_router import router as agent_analysis_router
from app.agent.api.v1.report_router import router as agent_report_router
from app.agent.api.v1.student_router import router as agent_student_router
from app.agent.api.v1.mock_router import router as agent_mock_router

app.include_router(agent_analysis_router, prefix="/api/v1/agent")
app.include_router(agent_report_router, prefix="/api/v1/agent")
app.include_router(agent_student_router, prefix="/api/v1/agent")
app.include_router(agent_mock_router, prefix="/api/v1/agent")
```

---

## 4. 数据流

### 4.1 分析请求流程（F1-F5，无 LLM）

```
Client
  │ POST /api/v1/agent/analysis/weak-points
  │ { class_id: 1, exam_ids: [1,2,3] }
  ▼
analysis_router.py
  │ 参数校验（Pydantic Schema）
  ▼
weak_point_engine.py  (service 层)
  │
  ├─→ score_record_repo.py   → SQL 聚合查询（GROUP BY kp, AVG score）
  ├─→ knowledge_point_repo.py → 知识点层级树 + 依赖 DAG
  ├─→ metrics.py             → kp_mastery_rate(), class_deviation(), discrimination_idx()
  ├─→ question_quality.py    → 低区分度题目降权
  └─→ tier_rules.json        → 读取薄弱判定阈值
  │
  ▼
返回结构化 JSON { knowledge_points: [...], summary }
```

### 4.2 报告生成流程（F6，含 LLM，异步）

```
Client
  │ POST /api/v1/agent/reports/generate
  │ { class_id: 1, exam_ids: [1,2,3], modules: ["weak-points","tiered-teaching","student-lists"] }
  ▼
report_router.py
  │ 1. 生成 task_id
  │ 2. asyncio.create_task(后台执行)
  │ 3. 立即返回 { task_id }
  ▼
report_service.py（后台异步执行）
  │
  ├─→ 依次调用 F1-F5 分析引擎 → 收集所有结构化数据
  │
  ├─→ 组装 Prompt（结构化数据填入模板）
  │
  ├─→ openai.ChatCompletion.create() → LLM 返回 JSON
  │
  ├─→ SuggestionItem Pydantic 校验
  │   ├─ 通过 → 继续
  │   └─ 失败 → 重试（最多2次），仍失败则降级为纯统计数据
  │
  └─→ 结果存入 task_store[task_id] = { status: "completed", data: {...} }

Client
  │ GET /api/v1/agent/reports/{task_id}
  ▼
返回 { status: "completed", report: {...} }
```

---

## 5. 开发流程（严格按顺序）

### Phase 1：基础设施（预计 3-4 天）

```
Step 1.1  创建 agent 目录骨架
          app/agent/__init__.py, models/, schemas/, repositories/,
          services/, api/v1/, core/, mock/ 全部建好空文件

Step 1.2  实现 ORM 模型（7 个表）
          Subject, KnowledgePoint, KnowledgeDependency, Question,
          QuestionKnowledgePoint, Exam, ScoreRecord
          注册到 core/database.py 的 Base.metadata（不改动 database.py 本身）

Step 1.3  实现 metrics.py
          8-9 个核心指标函数，纯 Python，可独立单元测试
          输入: DataFrame/数值，输出: float
```

### Phase 2：Mock 数据（预计 2-3 天）

```
Step 2.1  实现 student_profile.py
          随机生成 270 个学生的画像参数（6 维度）

Step 2.2  实现 knowledge_tree.py
          生成约 30 个知识点（三级树）+ 依赖关系 DAG + 144 道题目

Step 2.3  实现 score_generator.py
          基于学生画像 × 知识点 × 题目，生成 6 次考试的成绩记录（约 38,880 条）

Step 2.4  实现 CLI + API 双入口
          python -m app.agent.mock generate
          POST /api/v1/agent/mock/generate
```

### Phase 3：分析引擎（预计 5-7 天）

```
Step 3.1  实现 question_quality.py
          题目区分度 + 实际难度系数计算

Step 3.2  实现 weak_point_engine.py（F1）
          依赖：metrics + question_quality + repository

Step 3.3  实现 tier_engine.py（F4）
          四层分层（含保护规则）

Step 3.4  实现 student_list_engine.py（F5）
          培优补差名单 + 多维度判定

Step 3.5  实现 trend_engine.py（F2）+ kp_comparison_engine.py
          趋势 + 跨考试知识点对比

Step 3.6  实现 enrollment_engine.py（F3）
          仅初三，升学形势分析

Step 3.7  编写 API Router（F1-F5 端点）
```

### Phase 4：Agent 化（预计 3-4 天）

```
Step 4.1  实现 report_service.py
          组装 Prompt + LLM 调用 + JSON Schema 校验 + 重试

Step 4.2  实现异步任务管理
          task_store dict + 轮询 GET 接口

Step 4.3  Prompt 调优
          针对初中数学教研语言微调
```

### Phase 5：测试与联调（预计 2-3 天）

```
Step 5.1  metrics.py 单元测试（确定性计算验证）
Step 5.2  分析引擎集成测试（Mock 数据输入 → 预期输出验证）
Step 5.3  API 集成测试（请求 → 响应结构验证）
Step 5.4  LLM 输出质量抽样检查
```

---

## 6. 关键设计决策

### 6.1 与现有 SIMS 表的隔离

- agent 的 `ScoreRecord` 表完全独立，通过 `student_no` 关联现有 `students` 表做 JOIN 查询
- agent 的 repository 只读现有 students/classes 表，不写入
- 如果未来需要接入真实成绩数据，只需修改 repository 的数据源

### 6.2 规则配置热加载

```python
# app/agent/core/config/__init__.py
import json
from pathlib import Path

class TierConfig:
    _instance = None

    def __init__(self):
        self._path = Path(__file__).parent / "tier_rules.json"
        self._data = self._load()

    def _load(self):
        with open(self._path) as f:
            return json.load(f)

    def reload(self):
        """热重载配置，无需重启服务"""
        self._data = self._load()

    @property
    def tier_a_percent(self):
        return self._data["tier_rules"]["A"]["rank_percent"]

    # ... 其他配置项

config = TierConfig()  # 全局单例
```

### 6.3 LLM 调用重试与降级

```python
async def generate_report(data: dict, max_retries: int = 2):
    for attempt in range(max_retries + 1):
        try:
            raw = await call_llm(data)
            validated = AnalysisReport.model_validate(raw)
            return validated
        except ValidationError:
            if attempt < max_retries:
                continue  # 重试
            # 降级：返回纯统计数据，不强制 LLM 输出
            return fallback_report(data)
```

---

## 7. 文件创建顺序总览

```
Phase 1（基础设施）
  app/agent/__init__.py
  app/agent/models/__init__.py
  app/agent/models/subject.py
  app/agent/models/knowledge_point.py
  app/agent/models/knowledge_dependency.py
  app/agent/models/question.py
  app/agent/models/question_kp.py
  app/agent/models/exam.py
  app/agent/models/score_record.py
  app/agent/schemas/__init__.py
  app/agent/schemas/suggestion.py
  app/agent/schemas/analysis_request.py
  app/agent/schemas/analysis_response.py
  app/agent/schemas/report.py
  app/agent/core/__init__.py
  app/agent/core/metrics.py
  app/agent/core/config/__init__.py
  app/agent/core/config/tier_rules.json
  app/agent/repositories/__init__.py
  app/agent/repositories/score_record_repo.py
  app/agent/repositories/knowledge_point_repo.py
  app/agent/repositories/exam_repo.py
  app/agent/repositories/student_repo.py
  app/agent/services/__init__.py
  app/agent/api/__init__.py
  app/agent/api/v1/__init__.py
  app/agent/mock/__init__.py

Phase 2（Mock 数据）
  app/agent/mock/student_profile.py
  app/agent/mock/knowledge_tree.py
  app/agent/mock/score_generator.py
  app/agent/mock/cli.py
  app/agent/api/v1/mock_router.py

Phase 3（分析引擎）
  app/agent/services/question_quality.py
  app/agent/services/weak_point_engine.py
  app/agent/services/tier_engine.py
  app/agent/services/student_list_engine.py
  app/agent/services/trend_engine.py
  app/agent/services/kp_comparison_engine.py
  app/agent/services/enrollment_engine.py
  app/agent/api/v1/analysis_router.py
  app/agent/api/v1/student_router.py

Phase 4（Agent 化）
  app/agent/services/report_service.py
  app/agent/api/v1/report_router.py

Phase 5 的改动点
  app/main.py（新增 router 注册）
```

---

## 8. 前置确认

开始 Phase 1 前需要确认：

- [ ] MySQL 数据库可连接，有建表权限
- [ ] `.env` 文件已有 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME
- [ ] Python 3.12+ 环境可用，`uv sync` 可正常执行
- [ ] 当前在 `feature/teaching-optimization-agent` 分支开发
- [ ] 需要额外安装的包：`pandas`, `openai`, `faker`（通过 `uv add` 添加）
