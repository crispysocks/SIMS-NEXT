# 升学预测平台 v2.0 设计文档

> **状态：** 待实现
> **版本：** v2.0
> **日期：** 2026-05-28
> **定位：** 结合方案一（Chat设计）+ 方案二（V4.0）精华，落地可执行版本

---

## 一、背景与目标

### 现状问题
1. **预测不可解释** — 学生看到"冲刺L3学校，概率65%"，不明白为什么
2. **模糊区间准确率低** — 纯规则引擎在分数差 -30~30 区间只有 60% 准确率
3. **位次概念未落地** — V4.0 强调位次为核心，但代码仍是分数差判断

### v2.0 目标
1. **可解释的预测** — Chat 接口用自然语言告诉学生预测理由
2. **更准确的预测** — 位次为核心 + XGBoost 混合架构
3. **稳定落地** — 不贪心，优先实现 Chat + 位次改造 + ML 集成

---

## 二、核心架构

### 2.1 架构图

```
用户请求
    │
    ▼
┌──────────────────────────────────────┐
│            API 层                     │
│                                      │
│  GET  /api/v1/advice/{student_id}   │ ← 已有，改造
│  POST /api/v1/advice/{student_id}/chat│ ← 新增，流式SSE
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│            服务层                     │
│                                      │
│  ChatService (新增)                  │
│    ├── PredictionService             │
│    ├── PortraitService               │
│    ├── RiskService                   │
│    └── RegionalCompetitionService    │
│                                      │
│  PredictionService (改造)            │
│    ├── 规则引擎（明确区间）            │
│    ├── XGBoost（模糊区间）            │
│    └── 位次为核心                     │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│            数据层                     │
│                                      │
│  新增：chat_sessions                 │
│  改造：score_rank_lines 优先使用      │
│  预留：behavior_features, regional_exam_stats
└──────────────────────────────────────┘
```

### 2.2 改造 PredictionService（位次为核心）

**原逻辑（分数差）：**
```python
if score_diff > 30:
    ad_type = "保底"
elif score_diff < -30:
    ad_type = "冲刺"
```

**新逻辑（位次为核心）：**
```python
# 核心指标：rank_diff = 学生预测位次 - 学校录取位次
rank_diff = student_predicted_rank - school.admission_rank

if rank_diff > 500:       # 远超录取线
    ad_type = "保底"
    probability = 85-95%
elif rank_diff > -200:    # 接近录取线
    ad_type = "稳定"
    probability = 50-85%
elif rank_diff > -1000:   # 低于录取线
    ad_type = "冲刺"
    probability = 30-50%
else:                      # 差很远
    ad_type = "冲刺"
    probability = 10-30%

# 分数差作为辅助微调（±5%）
```

**为什么用位次更稳：**
- 分数随题目难度波动，位次更稳定
- 高中录取本质是位次竞争，不是分数竞争

### 2.3 XGBoost 混合架构

```
请求进入 PredictionService
    │
    ├── rank_diff 明确（>70% 或 <30%概率）
    │   └── 直接规则引擎返回
    │
    └── rank_diff 模糊（30%-70%概率区间）
        ├── 提取特征（9个特征，见下表）
        ├── XGBoost 推理 → P_ml
        ├── 规则引擎 → P_rule
        └── 加权融合：P = w × P_rule + (1-w) × P_ml
                     w 根据置信度动态调整
```

**特征工程（9个特征）：**

| 特征名 | 来源 | 说明 |
|--------|------|------|
| student_score | 传入 | 学生当前分数 |
| student_rank | 一分一段表 | 学生预测位次 |
| school_admission_rank | admission_lines | 学校录取位次 |
| rank_diff | 计算 | 位次差 |
| enrollment_count | admission_lines | 招生人数 |
| ranking_stability | exam_records | 排名稳定性因子 |
| score_volatility | exam_records | 成绩波动系数 |
| historical_trend | admission_lines | 历年录取线趋势 |
| regional_factor | score_rank_lines | 区域竞争因子 |

**XGBoost 配置：**
```python
model = xgboost.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    objective='binary:logistic',
    eval_metric='auc'
)
```

**训练数据：**
- 1000+ 条历史录取记录（学生ID + 录取学校 + 年份）
- 每月1日自动训练

### 2.4 Chat 接口设计

```
POST /api/v1/advice/{student_id}/chat
    │
    ├── 查 chat_sessions（5分钟内活跃会话）
    ├── 判断 message_count
    │   ├── 0 → 精简上下文（约500-800 tokens）
    │   ├── 1-2 → 完整上下文（约1500-2000 tokens）
    │   └── ≥3 → 创建新session，丢弃旧会话
    │
    ├── 构建 Prompt
    ├── 调用 DeepSeek API（stream=True）
    └── SSE 流式返回
```

**流式响应格式：**
```
data: {"content": "根据你的情况...", "done": false}
data: {"content": "你的排名...", "done": false}
...
data: {"content": "[DONE]", "done": true}
```

**会话状态机：**
```
用户发请求 → 查5分钟内活跃会话
           │
           ├─ 无会话 → 创建新session，message_count=0
           ├─ message_count < 3 → 追加消息
           └─ message_count >= 3 → 创建新session
```

**上下文策略：**

| 会话轮次 | 上下文类型 | 内容 |
|----------|-----------|------|
| 首轮（0） | 精简版 | 核心结论（分数、排名、预测分类、建议） |
| 追问（1-2） | 完整版 | 首轮内容 + 追问内容 |

**截断策略（防止token溢出）：**
- 首轮精简：保留关键3所学校（冲刺/稳定/保底各1所）
- 追问完整：保留最近2轮对话 + 当前问题

### 2.5 RegionalCompetitionService（轻量版）

利用现有的 `score_rank_lines` 表计算：

```python
def calculate_regional_competition(region: str, year: int) -> dict:
    """
    基于一分一段表计算区域竞争指数
    """
    # 高分段比例 = 前10%学生数 / 总考生数
    # 返回竞争指数 0.0 ~ 1.0
```

---

## 三、数据模型

### 3.1 新增表：chat_sessions

```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    message_count INTEGER DEFAULT 0,
    messages TEXT DEFAULT '[]',
    last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student_id (student_id),
    INDEX idx_last_active (last_active_at)
);
```

**messages 字段格式：**
```json
[
  {"role": "user", "content": "我想冲L3学校有可能吗？"},
  {"role": "assistant", "content": "根据你的情况..."}
]
```

### 3.2 预留表（本期不实现）

| 表名 | 用途 | 状态 |
|------|------|------|
| behavior_features | 学习行为数据 | 预留，等数据完备 |
| regional_exam_stats | 区域考试统计 | 轻量版可用 score_rank_lines 替代 |

---

## 四、API Schema

### 4.1 Chat 接口

**POST /api/v1/advice/{student_id}/chat**

请求体：
```python
class ChatRequest(BaseModel):
    message: Optional[str] = None  # 追问内容，首轮为空
    stream: bool = True
```

响应（SSE流式）：
```python
class ChatStreamEvent(BaseModel):
    content: str
    done: bool = False
```

### 4.2 错误码

| HTTP状态 | 错误信息 | 场景 |
|----------|---------|------|
| 404 | "学生不存在" | student_id无效 |
| 404 | "暂无考试成绩数据" | 无ExamRecord |
| 404 | "请先进行预测评估" | 无Prediction数据 |
| 503 | "服务繁忙，请稍后重试" | LLM调用超时/失败 |

---

## 五、服务依赖

```
ChatService
    ├── PredictionService（获取预测结果）
    ├── PortraitService（获取学习画像）
    ├── RiskService（获取风险标签）
    └── RegionalCompetitionService（获取区域竞争因子）

PredictionService
    ├── 规则引擎（明确区间，|rank_diff| > 500）
    ├── XGBoost模型（模糊区间）
    └── ModelLoader（加载 admission_model_vX.pkl）

ModelLoader
    └── 支持版本管理（v1, v2, ...）
```

---

## 六、文件结构

```
app/predict/
├── models/
│   ├── chat_session.py           # 新增：ChatSession ORM
│   └── ... (已有)
├── schemas/
│   └── chat.py                   # 新增：ChatRequest, ChatStreamEvent
├── repositories/
│   └── chat_session_repository.py  # 新增：会话CRUD
├── services/
│   ├── chat_service.py           # 新增：对话逻辑 + LLM调用
│   ├── regional_service.py       # 新增：区域竞争计算
│   ├── prediction_service.py     # 改造：位次为核心 + ML混合
│   └── ... (已有)
├── ml/
│   ├── model_loader.py           # 改造：版本管理
│   └── train_admission_model.py  # 改造：特征工程更新
└── api/v1/
    └── advice_router.py          # 改造：新增 /chat 端点

scripts/
└── create_tables.sql             # 改造：新增 chat_sessions 表
```

---

## 七、实现计划

### Phase 1（1-2周，可测试）

| 任务 | 说明 |
|------|------|
| T1 | 新增 chat_sessions 表 + ORM |
| T2 | 新增 ChatSession Repository |
| T3 | 新增 ChatRequest/ChatStreamEvent Schema |
| T4 | 新增 ChatService（会话管理 + LLM调用） |
| T5 | 新增 /chat 端点（流式SSE） |
| T6 | 改造 PredictionService（位次为核心） |

### Phase 2（1周）

| 任务 | 说明 |
|------|------|
| T7 | XGBoost 训练脚本 + 特征工程 |
| T8 | 改造 ModelLoader（版本管理） |
| T9 | 改造 PredictionService 集成ML混合 |
| T10 | 新增 RegionalCompetitionService |

### Phase 3（0.5周）

| 任务 | 说明 |
|------|------|
| T11 | AdviceGuard Prompt 层安全过滤 |
| T12 | 联调测试 |

---

## 八、自检清单

- [x] Spec覆盖：Chat接口、会话管理、提示词、ML升级、位次改造均已覆盖
- [x] 无占位符：所有设计项均有具体实现方案
- [x] 类型一致性：API Schema、提示词变量、数据模型一致
- [x] 依赖清晰：ChatService和PredictionService依赖已标注
- [x] 范围可控：只做1个新表，其他预留
- [x] 分期明确：Phase 1/2/3 划分清晰

---

**设计文档版本：** v2.0
**更新日期：** 2026-05-28
**状态：** 待实现