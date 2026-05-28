# AI Tutor — 系统架构

## 设计原则

| 原则 | 含义 |
|------|------|
| **Local-first** | 无数据库、纯内存运行。LLM 层可选，失败不影响核心 |
| **Deterministic** | 相同 seed + 相同答题序列 → 完全相同的轨迹 |
| **Flat architecture** | 7 个模块文件，无嵌套，无框架抽象 |
| **Pure Python** | 除 FastAPI/Streamlit (ui/streamlit_app.py) 外，核心逻辑零依赖框架 |
| **Explainable** | 推荐结果自带 `reason` 字段，掌握度可追溯 |

## 模块职责

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   engine.py  │    │  mastery.py  │    │recommender.py│    │tutor_agent.py│
│              │    │              │    │              │    │              │
│ 出题生成      │    │ 掌握度追踪    │    │ 题目推荐      │    │ LLM 教学反馈  │
│ 答案验证      │    │ 不确定性量化   │    │ 难度调节      │    │ 解析/提示/鼓励 │
│ SymPy 安全层  │    │ Beta-Binomial │    │ 挫折保护      │    │ 失败安全      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       └───────────────────┼───────────────────┼───────────────────┘
                           │                   │
                    ┌──────┴───────────────────┴──────┐
                    │          session.py              │
                    │                                 │
                    │ 教学会话编排                      │
                    │ 状态管理                         │
                    │ 进度追踪                         │
                    └─────────────────────────────────┘
```

### 1. engine.py — 出题引擎

**职责**：确定性生成数学题，验证学生答案。

- 5 个知识点 × 3 个难度 = 15 个模板
- 每个模板逆向出题：先随机选答案，再构造题目（保证可解）
- `safe_parse()` / `safe_compare()` 包装所有 SymPy 交互，永不崩溃
- `seed` 控制 `random.Random`，保证完全可复现

**知识点覆盖：**

| 知识点 | 依赖 | 示例 |
|--------|------|------|
| `linear_equation` | — | `2x + 3 = 7` |
| `quadratic_equation` | linear_equation | `x² + 5x + 6 = 0` |
| `factoring` | linear_equation | 因式分解 `x² - 4` |
| `derivative` | linear_equation | 求导 `d/dx (x³)` |
| `integral` | derivative | 积分 `∫ x² dx` |

### 2. mastery.py — 掌握度追踪

**职责**：基于 Beta-Binomial 贝叶斯模型追踪学生对每个知识点的掌握程度。

- 先验：Beta(α=3, β=3)，均值 0.5，高不确定性
- 答对：α += 1；答错：β += 1
- `mastery = α/(α+β)` — 后验均值（预估正确率）
- `variance` — 后验方差（不确定性），用于推荐 tie-breaking
- 纯 in-memory dict 存储，无数据库

**为什么不用 EMA：**
- EMA 对小样本不稳定（初始几次波动剧烈）
- Beta 保留不确定性信息（小 N → 宽分布，大 N → 窄分布）
- 自然解释："见过 α 次成功，β 次失败"

### 3. recommender.py — 题目推荐

**职责**：根据掌握度状态，决定下一题的 topic 和 difficulty。

**三层推荐策略（按优先级）：**

| 层级 | 条件 | 策略 | 目的 |
|------|------|------|------|
| **挑战区** | mastery ∈ [0.4, 0.7] | 选方差最大的（最不确定） | 最大化学习收益 |
| **巩固区** | mastery < 0.4 | 选 mastery 最高的（最接近入门） | 最低努力进入挑战区 |
| **复习区** | mastery > 0.7 | 选 mastery 最低的（最可能遗忘） | 螺旋复习防遗忘 |

**前置门槛**：某 topic 的前置知识点 mastery < 0.6 → 阻止该 topic。

**挫折保护**：连续 3 题答错 → 降低一档难度 + 切换 topic。

**难度映射**：mastery < 0.4 → easy, 0.4-0.7 → medium, > 0.7 → hard。

### 4. session.py — 会话编排

**职责**：串联 engine + mastery + recommender + tutor_agent 为完整的教学循环。

```
next_question()
  → recommender.recommend()  → 选出 topic + difficulty
  → engine.generate()        → 生成题目
  → 返回 Question

submit_answer(student_answer)
  → safe_compare()           → 对错判断
  → mastery.update()         → 更新掌握度
  → recommender.record()     → 记录历史（用于挫折检测）
  → tutor_agent.get_feedback() → LLM 教学反馈（可选）
  → 更新 streak + history
  → 返回 AnswerFeedback（含 tutor_response）
```

**状态追踪**：`SessionState` 保存当前题目、连对/连错次数、完整答题历史。

### 5. tutor_agent.py — LLM 教学反馈

**职责**：调用 LLM 生成教学反馈，仅用于教学交互。

- **不参与**对错判断、掌握度更新、题目推荐——确定性核心保持权威
- 输入：topic、difficulty、question_text、student_answer、correct_answer、is_correct
- 输出：`TutorResponse`（explanation、hint、encouragement）或 `None`
- 失败安全：无 API key / 网络错误 / 解析失败 → 返回 `None`，核心循环不受影响
- 支持 mock 模式用于测试
- OpenAI 兼容接口：`urllib.request`（stdlib），通过环境变量配置
- `.env` 文件加载 API key、base URL、model name

## 数据流

```
学生答题 "x=3"
     │
     ▼
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌───────────────┐
│ safe_compare │────▶│ mastery.update│────▶│recommender.   │     │ tutor_agent   │
│ (对/错)      │     │ (α/β 更新)    │     │record(对/错)  │     │.get_feedback  │
└─────────────┘     └──────────────┘     └───────────────┘     │ (可选,教学反馈) │
       │                                                       └───────┬───────┘
       │  确定性核心 (authoritative)                                     │  教学层 (advisory)
       └──────────────────────────────┬─────────────────────────────────┘
                                      ▼
                             ┌───────────────┐
                             │ AnswerFeedback │
                             │ + TutorResponse│
                             └───────────────┘
```

## 关键设计决策

| 决策 | 理由 |
|------|------|
| **不存题目** | 每次现场生成，无需题库维护 |
| **逆向出题** | 先选答案再构造题 → 保证可解，避免退化 |
| **Beta 先验 3/3** | 对称、非信息性、从一开始就稳定 |
| **tuple 答案比较** | `safe_compare` 显式处理逗号分隔的多值答案（如二次方程两根） |
| **LLM 仅教学层** | 对错判断、掌握度、推荐全部确定性，LLM 只生成文字反馈 |
| **Session 无状态机** | 显式 `next → submit → next` 顺序，不引入状态模式 |
| **Recommender 无策略模式** | 简单 if-else 三层选择，可读性优于可扩展性 |

## 测试覆盖率

| 模块 | 测试数 | 覆盖重点 |
|------|--------|----------|
| engine | 115 | 15 模板正确性、安全性、确定性 |
| mastery | 19 | Beta 更新、方差、收敛性 |
| recommender | 30 | 三层策略、挫折保护、门槛 |
| session | 38 | 完整循环、streak、历史、确定性 |
| tutor_agent | 18 | mock 模式、fallback、prompt 格式、session 集成 |
| API | 20 | 端点正确性、错误处理、确定性 |
| UI smoke | 13 | 交互流程、重置、进度数据 |
| **总计** | **253** | |
