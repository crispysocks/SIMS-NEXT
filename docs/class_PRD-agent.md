# 班级教学优化 Copilot — 产品需求文档（V1.0）

## 1. 产品概述

### 1.1 产品定位

**班级教学优化 Copilot** 是一个面向初中教师的 AI 辅助教学决策系统。核心目标：

> 用 AI 帮老师完成"班级教学诊断 + 教学决策"，而不是做一个聊天机器人。

### 1.2 核心用户

| 用户 | 使用场景 |
|------|---------|
| 班主任 | 全局掌握班级学业状况，定位问题学生 |
| 学科老师（数学） | 诊断班级薄弱知识点，调整教学节奏 |
| 年级主任 | 横向对比各班，评估教学质量 |

### 1.3 核心原则

1. **先分析引擎，后 Agent 外壳** — 统计计算由规则引擎完成，LLM 只负责自然语言建议生成
2. **规则 + LLM 混合** — 规则负责统计/排序/阈值判断（稳定可解释），LLM 负责建议/总结/解释（灵活表达）
3. **工作流 Agent，非自由 Agent** — 教育场景需要可控、可解释、可复现，严禁模型自由发挥
4. **建议可追溯** — 每一条教学建议必须附带数据依据，老师能反向验证

---

## 2. 教师痛点与解决方案

| 痛点 | 现状 | 本系统方案 |
|------|------|-----------|
| 分析班级薄弱知识点 | 手工翻试卷、凭印象 | 自动聚合错误率+区分度+年级偏差，输出薄弱点 Top N |
| 找临界生 | Excel 手动排序筛选 | 按多维度自动识别临界生，附带数据依据 |
| 分层教学 | 靠经验划分 | 四层分层（A/B/C/D），每层自动生成教学策略 |
| 判断升学趋势 | 凭感觉 | 历次考试趋势折线 + 高中分数线对标 |
| 培优补差名单 | 主观判断 | 多维度算法（波动率+成长性+单科短板）自动生成 |
| 课堂节奏调整 | 没数据支持 | 基于知识点掌握率分布，建议哪些知识点补课时 |

---

## 3. MVP 范围

### 3.1 第一阶段范围

仅做 **初中数学**，所有数据 Mock 生成。

### 3.2 核心功能

| # | 功能 | 输入 | 输出 |
|---|------|------|------|
| F1 | 薄弱知识点汇总 | 班级 + 考试范围 | 按知识点排序的薄弱清单，含错误率/区分度/年级偏差 |
| F2 | 成绩趋势分析 | 班级 + 时间范围 | 班级均分走势、知识点掌握率变化趋势 |
| F3 | 升学形势分析 | 初三班级 | 高中上线预估、临界生名单、风险预警 |
| F4 | 分层教学建议 | 班级 + 最近考试 | 四层学生名单（A/B/C/D）+ 每层教学策略 |
| F5 | 培优补差名单 | 班级 + 最近考试 | 培优名单 + 补差名单，含具体薄弱点和针对性建议 |
| F6 | 综合建议报告 | 以上全部 | LLM 生成自然语言教学优化报告 |

### 3.3 暂不做的

- 多学科支持（V2）
- 高中阶段（V2）
- 多 Agent 协作（V2）
- 教案/作业自动生成（V2）
- Excel 导入（V1 用 Mock 数据替代，V2 做）

---

## 4. 数据模型设计

### 4.1 新增表结构

#### 科目表 `subjects`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增 |
| name | VARCHAR(50) | 科目名称（V1 仅"数学"） |
| category | VARCHAR(20) | 文科/理科/综合 |
| is_deleted | BOOLEAN | 软删除 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 知识点表 `knowledge_points`

支持三级层级，例如：函数 → 二次函数 → 顶点公式

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增 |
| subject_id | INT FK | 所属科目 |
| name | VARCHAR(100) | 知识点名称 |
| parent_id | INT FK | 父级知识点（NULL = 一级） |
| level | TINYINT | 层级（1/2/3） |
| is_deleted | BOOLEAN | 软删除 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 题目表 `questions`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增 |
| subject_id | INT FK | 所属科目 |
| content | VARCHAR(500) | 题目内容简述 |
| difficulty | TINYINT | 难度（1基础/2中等/3拔高/4压轴） |
| question_type | VARCHAR(20) | 题型（选择/填空/解答） |
| max_score | DECIMAL(5,2) | 题目满分值 |
| is_deleted | BOOLEAN | 软删除 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 题目-知识点关联表 `question_knowledge_points`

多对多关系：一道题可涉及多个知识点

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增 |
| question_id | INT FK | 题目 ID |
| knowledge_point_id | INT FK | 知识点 ID |

#### 知识点依赖关系表 `knowledge_dependencies`

`parent_id` 只能表达树形层级，但真实学科知识是 DAG 图。例如"二次函数差"的根因可能是"因式分解没学好"，这需要跨分支依赖来表达。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增 |
| source_kp_id | INT FK | 前置知识点 ID |
| target_kp_id | INT FK | 依赖于此前置知识点的目标知识点 ID |
| dependency_weight | DECIMAL(3,2) | 依赖权重（0~1，越大表示前置越关键） |

示例数据：

```
因式分解(source) → 一元二次方程(target)   weight=0.9
一元一次方程(source) → 一次函数(target)   weight=0.7
一次函数(source) → 二次函数(target)       weight=0.8
相似三角形(source) → 圆综合(target)       weight=0.5
```

用途：分析薄弱知识点时，自动追溯前置依赖——如果"二次函数"薄弱且"因式分解"也薄弱，根因可能是因式分解而非二次函数本身。这是"AI 是否真正懂教学逻辑"的关键。

#### 考试表 `exams`

`exam_name` 不能只作为字符串使用，必须抽象为独立实体，否则跨学期/同名校级考试/趋势分析会出问题。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增 |
| name | VARCHAR(100) | 考试名称（月考1/期中考试 等） |
| grade | TINYINT | 年级（7初一/8初二/9初三） |
| term | VARCHAR(20) | 学期（上学期/下学期） |
| exam_type | VARCHAR(20) | 类型（月考/期中/期末） |
| exam_date | DATE | 考试日期 |
| subject_id | INT FK | 科目 ID（V1 固定为数学） |
| total_score | DECIMAL(5,2) | 满分值 |
| is_deleted | BOOLEAN | 软删除 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 成绩明细扩展表 `score_records`

按题目粒度的成绩记录。独立于现有 `scores` 表，不做修改。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增 |
| student_no | VARCHAR(20) | 学号 |
| exam_id | INT FK | 考试 ID（关联 exams 表） |
| question_id | INT FK | 题目 ID |
| score | DECIMAL(5,2) | 学生该题得分 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 4.2 实体关系图

```
subjects ──┬── knowledge_points ──┐
           │       │   │           │
           │       │   └── knowledge_dependencies（前置依赖DAG）
           │       │               │
           │       └── question_knowledge_points（多对多）
           │               │
           ├── questions ──┘
           │       │
           └── exams ─────┐
                   │       │
                   └── score_records（按题目粒度）
                           │
 students ─────────────────┘（通过 student_no 关联）
```

### 4.3 与现有 SIMS 表的关系

- `score_records.student_no` → 关联现有 `students.student_no`
- `exams.name` → 与现有 `scores.exam_name` 语义一致
- 不修改现有 `scores` 表，全部新表为独立扩展模块

---

## 5. 教育指标体系层（Metrics Layer）

> 所有分析模块统一引用本层定义的指标，保证系统一致性，避免各模块各自计算公式导致混乱。

### 5.1 核心指标定义

| 指标 ID | 名称 | 公式 | 说明 |
|---------|------|------|------|
| `kp_mastery_rate` | 知识点掌握率 | Σ 学生在该 KP 相关题目得分 / Σ 相关题目满分 / 学生数 | 核心指标 |
| `score_volatility` | 成绩波动率 | std(近 N 次考试总分) / 平均总分 | 衡量学生稳定性 |
| `growth_rate` | 成长率 | slope(近 N 次考试总分线性回归) | 衡量进步/退步速度 |
| `discrimination_idx` | 区分度 | 高分组得分率 - 低分组得分率 | 衡量知识点/题目的区分能力 |
| `class_deviation` | 年级偏差 | 班级得分率 - 年级平均得分率 | 判断是班级问题还是年级共性问题 |
| `basic_question_rate` | 基础题正确率 | 基础题（难度≤2）得分 / 基础题满分 | 衡量基础能力 |
| `challenge_question_rate` | 压轴题得分率 | 压轴题（难度=4）得分 / 压轴题满分 | 衡量拔高能力 |
| `consecutive_decline` | 连续下滑次数 | 连续考试总分下降的次数 | 风险预警信号 |
| `kp_consecutive_weak` | 持续薄弱次数 | 同一 KP 连续得分率 < 60% 的考试次数 | 顽固薄弱点识别 |

### 5.2 使用原则

- 所有分析引擎的计算函数必须引用指标层定义，不自行写公式
- 新增指标需先在指标层注册，再被分析模块引用
- 指标实现为独立的 `app/agent/metrics.py` 模块

---

## 6. 分析引擎设计（规则引擎）

> 这一层不涉及 LLM，纯 Python 统计分析。所有阈值和配置从规则配置层读取，不硬编码。

### 6.0 教育规则配置层

所有阈值和切分比例必须可配置，不能写死在代码里。使用 JSON/YAML 配置文件：

```json
{
  "tier_rules": {
    "A": { "rank_percent": [0, 20] },
    "B": { "rank_percent": [20, 60] },
    "C": { "rank_percent": [60, 80] },
    "D": { "rank_percent": [80, 100] },
    "protection": {
      "score_rate_above": 0.80,
      "min_tier": "B",
      "force_d_below_score": 60
    }
  },
  "weak_kp": {
    "mastery_rate_below": 0.60,
    "min_discrimination": 0.15,
    "class_deviation_threshold": -0.05
  },
  "advanced_student": {
    "total_score_percentile": 30,
    "kp_mastery_rate_below": 0.50,
    "volatility_above": 0.15
  },
  "remedial_student": {
    "total_score_percentile": 70,
    "kp_mastery_rate_below": 0.40,
    "consecutive_decline_count": 3
  },
  "borderline": {
    "score_line_margin": 10
  },
  "enrollment": {
    "target_score_line": 65,
    "risk_below": 20
  }
}
```

配置文件路径：`app/agent/config/tier_rules.json`，支持运行时热更新。

### 6.1 知识点掌握率计算

**定义**：某次考试中，班级在某知识点上的平均得分率。

```
知识点掌握率 = Σ(学生在该知识点相关题目的得分) / Σ(相关题目的满分) / 学生数
```

同时计算三个维度：

| 指标 | 计算方式 | 用途 |
|------|---------|------|
| 班级得分率 | 该班该知识点的平均得分率 | 主要判断依据 |
| 年级偏差 | 班级得分率 - 年级平均得分率 | 判断是班级特有问题还是年级共性问题 |
| 区分度 | 该知识点在高分组与低分组的得分率差距 | 判断该知识点是否适合分层教学 |

### 6.2 薄弱知识点判定

综合三个条件排序：
1. 班级得分率最低的 Top N（主要权重）
2. 年级偏差为负（班级显著低于年级）
3. 区分度 > 阈值（说明还有提升空间，不是"全班都不会"的极端情况）

输出格式：
```
二次函数：
  班级得分率：42%
  年级平均：61%
  年级偏差：-19%
  区分度：0.35（中等）
  重点失分子知识点：
    - 顶点公式（得分率 28%）
    - 对称轴（得分率 35%）
```

### 6.3 题目质量分析

不是所有题都值得分析。对每道题目基于答题数据计算实际质量指标：

| 指标 | 计算方式 | 用途 |
|------|---------|------|
| 实际难度系数 | 全班平均得分 / 题目满分 | 对比预设 difficulty，校验出题质量 |
| 区分度 | 前 27% 学生该题平均得分率 - 后 27% 平均得分率 | < 0.2 的题目不适合用于薄弱知识点判定 |
| 信度贡献 | 该题与总分的相关性 | 后续可扩展到 KR-20 / Cronbach α |

低区分度题目（< 0.2）在薄弱知识点分析中降权处理，避免"全班都不会的偏题"干扰分析结果。

### 6.4 学生四层分层

**分层规则**（混合判定，按优先级执行）：

```
优先规则 1：得分率 > 80%（即分数 > 满分的 80%）→ 强制不在 D 层，最低 B 层
优先规则 2：得分 < 60 分 → 强制 D 层
兜底规则：按总分排名百分比划分
  A 层（培优）：总分排名前 20%
  B 层（稳定）：总分排名 20% ~ 60%
  C 层（临界）：总分排名 60% ~ 80%（可上可下，最值得投入）
  D 层（高风险）：总分排名后 20%
```

规则优先级：**规则 1（>80% 保护）> 规则 2（<60 强制 D）> 规则 3（排名百分比）**

示例：
- 学生 A 考了 100/120（83.3%），排名班级后 20% → 规则 1 生效，至少归 B 层，不进入 D 层
- 学生 B 考了 55/120（45.8%），排名班级前 50% → 规则 2 生效，强制归 D 层
- 学生 C 考了 72/120（60%），排名班级后 15% → 规则 3 生效，归 D 层

每层输出：
- 学生名单
- 该层平均分 / 中位数
- 该层典型特征（如 C 层：基础计算可以，综合题薄弱）
- 教学策略建议

### 6.5 培优补差名单

#### 培优名单（A/B 层中有短板的学生）

判定条件（满足 2 条以上）：
- 总分排名前 30%，但有某个知识点得分率 < 50%
- 近 3 次考试波动率 > 15%（不稳定，有潜力可挖）
- 基础题得分率高但压轴题得分率低（冲击高分）

输出格式：
```
张三 | 总分排名 5/45 | 薄弱知识点：二次函数（得分率 42%），圆的综合（得分率 38%）
建议：加强压轴题训练，重点突破二次函数综合应用
```

#### 补差名单（C/D 层学生）

判定条件：
- 总分排名后 30%，且多个核心知识点得分率 < 40%
- 近 3 次考试持续下降趋势
- 基础题得分率也低（说明基础薄弱，不是粗心）

输出格式：
```
李四 | 总分排名 40/45 | 薄弱知识点：一元一次方程（得分率 25%），整式运算（得分率 30%）
建议：回归课本，先从七年级计算基础补起，暂不安排综合题
```

### 6.6 知识点对比分析（跨考试）

对每个学生，追踪同一知识点在历次考试中的得分率变化：

```
学生王五 — 二次函数 知识点掌握率变化：
  月考 1：35% → 月考 2：48% → 月考 3：52%（↑上升趋势，已接近及格）
  月考 4：45%（↓波动，需关注）
```

班级层面汇总：
- 统计每个知识点的班级掌握率走势
- 标记"持续薄弱"（连续 3 次 < 60%）、"在进步"、"在退步"、"波动"

### 6.7 升学形势分析（仅初三）

基于近 3-5 次考试成绩，对标模拟分数线：

```
本地普通高中预估线：65分（折算百分制）
班级上线人数：32/45（71%）

临界生（分数线 ±10 分内）：8人
高风险（低于分数线 20 分以上）：5人
```

输出：
- 上线预估（普高率 / 重点率）
- 临界生名单（最有提升空间）
- 各科对总分的贡献度分析

---

## 7. Agent 层设计

### 7.1 整体架构（分层）

```
┌────────────────────┐
│     前端应用层      │  Next.js / React
└────────────────────┘
          │
┌────────────────────┐
│   Agent Workflow   │  LangGraph（V2）+ 任务路由
└────────────────────┘
          │
┌────────────────────┐
│   教学分析引擎层    │  F1~F5 规则计算（纯 Python/Pandas）
│   - 薄弱知识点      │
│   - 分层/培优补差   │
│   - 趋势/升学      │
└────────────────────┘
          │
┌────────────────────┐
│  教育规则配置层     │  JSON DSL，运行时可调
└────────────────────┘
          │
┌────────────────────┐
│  教育指标体系层     │  统一指标定义（metrics.py）
└────────────────────┘
          │
┌────────────────────┐
│     数据层          │  MySQL + SQLAlchemy
└────────────────────┘
```

各分析模块按 DAG 思维设计为独立节点，后续接 LangGraph 时直接组装：

```python
class WeakPointAnalysisNode   # F1
class TrendAnalysisNode       # F2
class EnrollmentAnalysisNode  # F3
class TieredTeachingNode      # F4
class StudentListAnalysisNode # F5
class ReportGenerationNode    # F6
```

### 7.2 工作流 DAG

```
用户请求（班级 + 考试范围）
       │
       ▼
┌─ 任务路由 ─────────────────────┐
│  解析意图 → 确定调用哪些分析模块  │
└────────────────────────────────┘
       │
       ▼
┌─ 数据分析节点（规则引擎）────────┐
│  调用分析引擎，产出结构化统计数据  │
└────────────────────────────────┘
       │
       ▼
┌─ 规则引擎审核 ──────────────────┐
│  阈值校验、异常值过滤、数据完整性  │
└────────────────────────────────┘
       │
       ▼
┌─ LLM 生成建议 ─────────────────┐
│  结构化数据 + Prompt → 自然语言  │
│  - 教学建议                     │
│  - 趋势解读                     │
│  - 分层策略                     │
│  - 个性化点评                   │
└────────────────────────────────┘
       │
       ▼
┌─ 结果审核 ─────────────────────┐
│  检查建议是否有数据依据           │
│  过滤空泛/无依据的输出            │
└────────────────────────────────┘
       │
       ▼
    最终报告（结构化 JSON + Markdown）
```

### 7.3 规则 vs LLM 分工

| 层级 | 负责内容 | 原因 |
|------|---------|------|
| **规则引擎** | 统计计算、排序、阈值判断、风险分级、临界生判定 | 需要稳定性和可解释性，不能靠模型"猜" |
| **LLM** | 教学建议措辞、趋势解读、分层策略描述、个性化点评 | 需要自然语言表达和教学领域知识 |

### 7.4 LLM Prompt 与输出校验

#### Prompt 结构

```text
SYSTEM:
你是一位有 15 年初中数学教学经验的教研组长。
请基于以下班级数据分析，生成教学优化建议。

输出必须使用以下 JSON 格式。每一条建议对象必须包含全部 5 个字段，缺一不可。

## 建议约束
- knowledge_point: 针对哪个具体知识点
- target_students: 针对哪类学生（A/B/C/D 层，或具体名单）
- question_type: 针对哪种题型或能力（基础计算/综合应用/压轴题/审题能力）
- teaching_action: 具体可操作的教学行为（禁止空话）
- expected_goal: 可量化的提升目标

禁止使用以下空话：
"加强练习" "提高兴趣" "关注基础" "多做题目" "强化训练" "重视教学" "巩固知识" "注意方法"

正确示例：
{
  "knowledge_point": "一次函数图像识别",
  "target_students": "C层学生（张三、李四、王五等8人）",
  "question_type": "基础图像判断题",
  "teaching_action": "每天10道图像-解析式互译练习（难度1-2），先由教师示范图像→解析式的转化步骤，再让学生独立完成",
  "expected_goal": "两周内基础题正确率从当前52%提升至70%以上"
}

USER:
## 班级概况
初三(2)班，45人，分析范围：月考1 ~ 月考4

## 薄弱知识点
[结构化数据表格]

## 学生分层
[四层分层名单及统计数据]

## 趋势分析
[知识点掌握率变化趋势]

## 培优补差名单
[名单及多维度指标]

请输出 JSON，包含以下字段：
- weak_kp_remediation: [...]（优先补救知识点 Top 5，每个含 5 要素建议）
- tier_strategies: { A: [...], B: [...], C: [...], D: [...] }（每层教学策略，每条含 5 要素）
- borderline_intervention: {...}（临界生干预方案）
- overall_direction: "..."（总体教学优化方向，200字内）
```

#### JSON Schema 后端校验

Prompt 约束不足以完全防止 LLM 漏字段。后端必须增加结构化校验层：

```python
from pydantic import BaseModel, Field, validator

class SuggestionItem(BaseModel):
    knowledge_point: str = Field(..., min_length=2)
    target_students: str = Field(..., min_length=2)
    question_type: str = Field(..., min_length=2)
    teaching_action: str = Field(..., min_length=10)  # 太短 = 空话
    expected_goal: str = Field(..., min_length=5)

    @validator("teaching_action")
    def reject_empty_phrases(cls, v):
        banned = ["加强练习", "提高兴趣", "关注基础", "多做题目",
                   "强化训练", "重视教学", "巩固知识", "注意方法"]
        for phrase in banned:
            if phrase in v:
                raise ValueError(f"包含禁止空话: {phrase}")
        return v

class AnalysisReport(BaseModel):
    weak_kp_remediation: list[SuggestionItem]
    tier_strategies: dict[str, list[SuggestionItem]]
    borderline_intervention: list[SuggestionItem]
    overall_direction: str = Field(..., max_length=500)
```

校验失败的输出返回 LLM 重新生成（最多重试 2 次），确保最终输出结构完整、不含空话。

### 7.5 技术选型

| 层 | 技术 | 说明 |
|----|------|------|
| 分析引擎 | Pandas + SQL | 纯 Python 统计计算 |
| Web 框架 | FastAPI（复用现有项目） | 新增 router，不改动现有代码 |
| Agent 框架 | 第一阶段：Python + Prompt + 固定 Workflow | 不上 LangGraph |
| LLM | OpenAI API 兼容接口 | 可切换国产大模型 |
| 数据库 | MySQL + SQLAlchemy ORM | 复用现有基础设施 |
| Mock 数据 | Faker + 自定义脚本 | V1 全部 Mock |

---

## 8. API 设计

### 8.1 分析接口

```
POST /api/v1/agent/analysis/weak-points
  说明：薄弱知识点分析
  请求：{ class_id, exam_ids[], top_n? }
  响应：{ knowledge_points: [...], summary }

POST /api/v1/agent/analysis/trends
  说明：成绩趋势分析（支持跨考试知识点对比）
  请求：{ class_id, exam_ids[], knowledge_point_ids? }
  响应：{ trends: [...], student_details: [...] }

POST /api/v1/agent/analysis/enrollment
  说明：升学形势分析（仅初三）
  请求：{ class_id, target_score_line? }
  响应：{ enrollment_rate, borderline_students, risk_level }

POST /api/v1/agent/analysis/tiered-teaching
  说明：分层教学建议
  请求：{ class_id, exam_id }
  响应：{ tiers: {A, B, C, D}, strategies }

POST /api/v1/agent/analysis/student-lists
  说明：培优补差名单
  请求：{ class_id, exam_id }
  响应：{ advanced: [...], remedial: [...] }

GET /api/v1/agent/students/{student_no}/knowledge-points
  说明：单个学生知识点全貌（支持跨考试对比）
  请求参数：?exam_ids=1,2,3
  响应：{
    student: { student_no, name, class_name },
    knowledge_points: [
      {
        kp_name: "二次函数",
        kp_path: "函数 > 二次函数",
        exams: [
          { exam_name: "月考1", score_rate: 0.35, class_avg_rate: 0.58, rank_in_class: 40/45 },
          { exam_name: "月考2", score_rate: 0.48, class_avg_rate: 0.61, rank_in_class: 35/45 },
          ...
        ],
        trend: "rising",  // rising/falling/volatile/stable
        level: "weak"     // strong(>80%)/moderate(60-80%)/weak(<60%)
      },
      ...
    ],
    summary: { strongest_kps: [...], weakest_kps: [...], trending_up: [...], trending_down: [...] }
  }

GET /api/v1/agent/classes/{class_id}/students/top
  说明：班级排名前 N 名或前 X% 学生的知识点掌握汇总
  请求参数：?n=10 (前10名) 或 ?percent=20 (前20%) 或 ?tier=A (查询指定分层)
             &exam_id=1
  响应：{
    students: [
      {
        student_no, name, rank, total_score,
        strong_kps: [...],   // 掌握率 > 80%
        weak_kps: [...],     // 掌握率 < 60%
        tier: "A"
      },
      ...
    ],
    group_summary: {
      avg_score: 92.5,
      common_weak_kps: [...],   // 该群体共同薄弱知识点
      common_strong_kps: [...],
      tier_distribution: { A: 10, B: 0, C: 0, D: 0 }
    }
  }
```

### 8.2 报告接口

```
POST /api/v1/agent/reports/generate
  说明：生成综合建议报告（调用 LLM）
  请求：{ class_id, exam_ids[], modules[] }
  响应：{ task_id }（异步）

GET /api/v1/agent/reports/{task_id}
  说明：获取报告结果
  响应：{
    report_id,
    status: "processing" | "completed" | "failed",
    structured_data: {...},
    markdown_report: "..."
  }
```

### 8.3 Mock 数据接口（V1 专用）

```
POST /api/v1/agent/mock/generate
  说明：一键生成 Mock 数据（含学生画像）
  请求：{
    class_count: 6,           # 班级数量（初一2+初二2+初三2）
    students_per_class: 45,   # 每班人数
    exam_count: 6,            # 考试次数
    questions_per_exam: 24    # 每次考试题目数
  }
  响应：{ generated: {...统计信息} }

DELETE /api/v1/agent/mock/clear
  说明：清除所有 Mock 数据
```

---

## 9. 开发阶段

### 9.1 阶段一（当前）：分析引擎 + Mock 数据

**目标**：不依赖 LLM，纯统计输出可用结果

- [ ] 创建数据表（subjects, knowledge_points, knowledge_dependencies, questions, question_kps, exams, score_records）
- [ ] 实现教育指标体系层（`app/agent/metrics.py`）
- [ ] 实现规则配置层（`app/agent/config/tier_rules.json`）
- [ ] 编写学生画像驱动的 Mock 数据生成脚本
- [ ] 实现分析引擎（F1~F5 全部规则计算，引用指标层和配置层）
- [ ] 实现知识依赖 DAG 追溯（薄弱知识点自动关联前置依赖）
- [ ] 编写 API 接口
- [ ] 单元测试（验证统计逻辑正确性，规则计算与手工验算 100% 一致）

### 9.2 阶段二：Agent 化

**目标**：引入 LLM，生成自然语言报告

- [ ] 实现工作流 Agent（任务路由 + 规则引擎 + LLM 调用 + 结果审核）
- [ ] 实现 LLM 输出 JSON Schema 校验器（Pydantic Validator，含空话检测 + 重试机制）
- [ ] 实现建议模板约束（每条建议 5 要素验证）
- [ ] Prompt 工程与调优
- [ ] 异步报告生成
- [ ] 报告质量评估（抽样检查建议是否满足 5 要素，是否包含空话）

### 9.3 阶段三：体验优化

- [ ] Excel 成绩导入
- [ ] 多学科扩展
- [ ] 高中阶段支持
- [ ] LangGraph 工作流重构

### 9.4 阶段四：高级能力

- [ ] **教学行为库**：建立"问题模式 → 教学动作"映射知识库

  | 问题模式 | 教学动作 |
  |---------|---------|
  | 顶点公式不会 | 专项公式训练（每天 15 题公式套用） |
  | 审题差导致失分 | 图像转化训练（文字→图像→解题） |
  | 综合题薄弱 | 分步拆解训练（先分步打分，再合并） |
  | 基础计算出错 | 七年级回炉（针对性补前置知识点） |

- [ ] 教学数字孪生（模拟"如果强化XX知识点，预计提升X分"）
- [ ] 学生特征工程（K-means 聚类发现新型学生群体）
- [ ] AI 作业推荐
- [ ] 年级级别 Agent（横向班间对比、教师教学质量分析）
- [ ] 教案/家校沟通生成

---

## 10. Mock 数据策略

### 10.1 学生画像驱动的数据生成

**核心思路**：不随机生成分数，而是先为每个学生生成"能力画像参数"，再根据画像参数驱动成绩生成。这样 Mock 数据会呈现真实的学生个体差异和跨考试连贯性。

**学生画像参数**：

```python
{
  "student_no": "20240101",
  "name": "张三",
  "class_id": 1,
  "profile": {
    "math_talent": 0.82,       # 数学天赋（影响所有知识点的基线得分率）
    "stability": 0.44,         # 稳定性（值越低波动越大，0.44 = 容易波动）
    "carefulness": 0.71,       # 细心度（影响基础题/计算题的失分概率）
    "geometry_bias": 0.66,     # 几何偏好（>0.5 几何强于代数，<0.5 相反）
    "growth_tendency": 0.08,   # 成长倾向（每次考试的自然进步率）
    "exam_anxiety": 0.35       # 考试焦虑（值越高，期中/期末等大考发挥越差）
  }
}
```

**成绩生成流程**：

```
1. 随机生成学生画像参数（A 层学生 math_talent 偏高、stability 偏高）
2. 对每次考试中的每道题：
   a. 基线得分率 = math_talent × 题目知识点匹配度
   b. 加入 stability 噪声（稳定性低的学生波动大）
   c. 基础题额外受 carefulness 影响
   d. 几何题额外受 geometry_bias 影响
   e. 大考（期中/期末）额外受 exam_anxiety 影响
   f. 加入 growth_tendency 的累积效应（后一次考试基线略高于前一次）
3. 最终得分 = max(0, min(max_score, 基线得分率 × max_score + 随机噪声))
```

**数据生成原则**：
- 符合真实成绩分布（近似正态分布，但允许长尾）
- 同一学生同一知识点在多次考试中有连贯趋势（不是完全随机）
- A 层学生：高 talent + 高 stability → 基础题稳定高得分，压轴题波动
- D 层学生：低 talent + 低 stability + 低 carefulness → 大规模失分
- "偏科"学生：geometry_bias 极端值 → 几何强但代数弱（或反之）

### 10.2 Mock 数据范围

| 实体 | 数量 | 说明 |
|------|------|------|
| 班级 | 6 个 | 初一 2 班 + 初二 2 班 + 初三 2 班（支持班间对比） |
| 学生 | 45 × 6 = 270 人 | 每班 45 人 |
| 知识点 | ~30 个 | 初中数学，三层级结构 |
| 题目 | ~144 题 | 每知识点关联 4-6 题，难度分布 |
| 考试次数 | 6 次 | 月考1~4 + 期中 + 期末 |
| 成绩记录 | 270 × 24 × 6 = 38,880 条 | 学生 × 每考题目 × 考试次数 |

### 10.3 知识点层级示例

```
初中数学
├── 数与式
│   ├── 有理数运算
│   │   ├── 绝对值
│   │   └── 科学记数法
│   ├── 整式运算
│   │   ├── 合并同类项
│   │   └── 乘法公式
│   └── 分式
│       ├── 分式化简
│       └── 分式方程
├── 方程与不等式
│   ├── 一元一次方程
│   ├── 二元一次方程组
│   ├── 一元二次方程
│   │   ├── 根的判别式
│   │   └── 韦达定理
│   └── 不等式与不等式组
├── 函数
│   ├── 一次函数
│   │   ├── 图像与性质
│   │   └── 应用问题
│   ├── 二次函数
│   │   ├── 顶点公式
│   │   ├── 对称轴
│   │   └── 最值问题
│   └── 反比例函数
├── 几何
│   ├── 三角形
│   │   ├── 全等三角形
│   │   └── 相似三角形
│   ├── 四边形
│   │   └── 特殊四边形判定
│   └── 圆
│       ├── 圆周角定理
│       └── 切线性质
└── 统计与概率
    ├── 数据的统计描述
    └── 概率初步
```

---

## 11. 非功能性需求

### 11.1 可解释性

- 每条建议附带数据来源（哪个考试、哪个知识点、具体数值）
- 报告支持"点击查看原始数据"

### 11.2 稳定性

- 同一数据多次分析，结果一致（LLM 部分允许措辞差异，但核心结论不变）
- 规则引擎 100% 确定性

### 11.3 安全性

- 所有建议附带置信度或免责声明
- 升学预测明确标注"仅供参考，非正式升学指导"

---

## 12. 成功标准

| 指标 | 目标 | 衡量方式 |
|------|------|---------|
| 分析准确性 | 规则计算 100% 与手工验算一致 | 单元测试 |
| 建议可用性 | 超过 70% 的建议有具体数据依据 | 报告抽样审核 |
| 报告生成速度 | 异步 < 60 秒 | 性能测试 |

---

## 13. 参考资料

- 现有 SIMS PRD：[docs/PRD.md](./PRD.md)
- 项目 README：[README.md](../README.md)
- 教学建议设计思路：Chat GPT教学建议.txt（项目根目录）
