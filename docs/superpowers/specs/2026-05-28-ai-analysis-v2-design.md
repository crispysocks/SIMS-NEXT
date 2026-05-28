# AI智能分析模块 v2.1 设计文档

> **状态：** 待实现
> **版本：** v2.1
> **日期：** 2026-05-28
> **定位：** 修复"问非所答"问题 + 增加思考过程可见性

---

## 一、问题分析

### 1.1 现状问题

| 问题 | 表现 | 根因 |
|------|------|------|
| 问非所答 | 问"数学加10分概率"，AI答"无法确定" | prompt未明确simulation数据的含义和用法 |
| 历史记录不显示 | 追问时AI不记得上下文 | 前端未展示chat历史，或后端未传递 |
| 思考过程不透明 | 开发者无法看到AI分析链路 | 无trace机制 |

### 1.2 测试验证

通过 `test_chat_debug.py` 验证：

```
simulation数据: 加10分→463分, 学校:第三中学, 概率71%, 变化+0%

问题: "数学加10分概率提升多少？"
回答: "无法确定 - 当前无法分析单科加分情况"

问题: "我加10分能上什么学校？"
回答: "需要加分模拟数据才能给出建议"
```

**根因定位：**
- simulation是总分加10/15/20分的模拟，不是单科
- prompt没有说明这一区别，导致LLM困惑
- 追问时prompt未强制要求使用simulation数据

---

## 二、改造方案

### 2.1 修复"问非所答"

**改造 `build_prompt` 方法：**

```python
# 首轮Prompt（message_count == 0）
prompt = f"""学生总分{context.get('current_score', 0):.0f}分，排名{context.get('current_ranking', '?')}名（{context.get('ranking_trend', '波动')}）。
{predictions_text}
风险：{', '.join(context.get('risk', {}).get('risk_tags', [])) or '无'}

【加分模拟数据】（总分变化，非单科）：
{sim_text}

用户问题：{user_message}

请直接给出选项让用户选择，不要先解释原因。格式：
**问题分析**：[一句话说明]
**可选方案**：
A. [方案A]
B. [方案B]
C. [方案C]

重要：用户提到"XX科加X分"时，用【加分模拟数据】中的总分变化来回答。
"""

# 追问Prompt（message_count > 0）
prompt = f"""【历史对话】
{history_text}

当前情况：总分{context.get('current_score', 0):.0f}分，排名{context.get('current_ranking', '?')}名

【加分模拟数据】（总分变化，非单科）：
{sim_text}

用户追问：{user_message or '无'}

请直接给选项，不要先解释。如果追问涉及提分，格式：
**可选方案**：
A. 加{sim['score_increase']}分→{sim['new_score']:.0f}分，{sim['school_name']}概率{sim['probability']}%
B. ...

重要：必须基于【加分模拟数据】回答提分相关问题。
"""
```

**关键改动：**
1. simulation数据标记为"总分变化，非单科"，避免混淆
2. 增加 `**可选方案**` 格式示例，包含具体数据
3. 追问时强制要求使用simulation数据

### 2.2 增加思考过程可见性

#### 2.2.1 Trace装饰器

**新增 `app/predict/services/trace_service.py`：**

```python
import logging
import time
from functools import wraps
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TraceStep:
    def __init__(self, service: str, method: str, input_data: Any, output_data: Any = None, duration_ms: float = 0):
        self.service = service
        self.method = method
        self.input_data = input_data
        self.output_data = output_data
        self.duration_ms = duration_ms
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "method": self.method,
            "input": self.input_data,
            "output": self.output_data,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp
        }

class TraceService:
    _instance: Optional['TraceService'] = None
    _steps: list[TraceStep] = []

    @classmethod
    def get_instance(cls) -> 'TraceService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_step(self, service: str, method: str, input_data: Any, output_data: Any = None, duration_ms: float = 0):
        step = TraceStep(service, method, input_data, output_data, duration_ms)
        self._steps.append(step)
        logger.info(f"[{service}] {method} - {duration_ms:.1f}ms")

    def get_steps(self) -> list[TraceStep]:
        return self._steps

    def clear(self):
        self._steps.clear()

    @staticmethod
    def traceable(service_name: str):
        """装饰器：为服务方法自动添加trace"""
        def decorator(method):
            @wraps(method)
            def wrapper(*args, **kwargs):
                trace = TraceService.get_instance()
                start = time.time()

                # 简化输入日志（避免大对象）
                input_repr = str(args[1:])[:200] if len(args) > 1 else str(kwargs)[:200]

                try:
                    result = method(*args, **kwargs)
                    duration_ms = (time.time() - start) * 1000

                    # 简化输出日志
                    output_repr = str(result)[:200] if result else None

                    trace.add_step(
                        service=service_name,
                        method=method.__name__,
                        input_data=input_repr,
                        output_data=output_repr,
                        duration_ms=duration_ms
                    )
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start) * 1000
                    trace.add_step(
                        service=service_name,
                        method=method.__name__,
                        input_data=input_repr,
                        output_data=f"ERROR: {str(e)}",
                        duration_ms=duration_ms
                    )
                    raise

            return wrapper
        return decorator

def get_trace_service() -> TraceService:
    return TraceService.get_instance()
```

#### 2.2.2 改造 ChatService

```python
# app/predict/services/chat_service.py

from app.predict.services.trace_service import traceable, get_trace_service

class ChatService:
    @traceable("ChatService")
    def get_context(self, student_id: int, message_count: int) -> dict:
        # 原有逻辑不变
        ...

    @traceable("ChatService")
    def build_prompt(self, context: dict, user_message: Optional[str], message_count: int, session_messages: list = None) -> str:
        # 原有逻辑不变
        ...

    @traceable("ChatService")
    def _call_llm(self, prompt: str, message_count: int) -> str:
        # 原有逻辑不变
        ...

    def chat(self, student_id: int, message: Optional[str]) -> Generator[dict, None, None]:
        trace = get_trace_service()
        trace.clear()  # 每次chat开始前清空

        # 原有逻辑...
```

#### 2.2.3 改造 PredictionService

```python
# app/predict/services/prediction_service.py

from app.predict.services.trace_service import traceable

class PredictionService:
    @traceable("PredictionService")
    def predict_student_admission(self, student_id: int, student_score: float) -> StudentPrediction:
        # 原有逻辑不变
        ...

    @traceable("PredictionService")
    def _calculate_admission_probability(self, ...) -> int:
        # 原有逻辑不变
        ...
```

#### 2.2.4 改造 PortraitService / RiskService

```python
# app/predict/services/portrait_service.py

from app.predict.services.trace_service import traceable

class PortraitService:
    @traceable("PortraitService")
    def analyze_student(self, student_id: int) -> Optional[StudentPortrait]:
        # 原有逻辑不变
        ...

# app/predict/services/risk_service.py

from app.predict.services.trace_service import traceable

class RiskService:
    @traceable("RiskService")
    def analyze_risk(self, student_id: int) -> Optional[StudentRisk]:
        # 原有逻辑不变
        ...
```

#### 2.2.5 新增 debug 端点

```python
# app/predict/api/v1/advice_router.py

from app.predict.services.trace_service import get_trace_service
from app.predict.schemas.chat import ChatDebugResponse

@router.get("/{student_id}/debug")
def get_chat_debug(student_id: int, db: Session = Depends(get_db)):
    """获取上次chat的思考过程trace（仅debug模式）"""
    trace = get_trace_service()
    steps = trace.get_steps()

    return ChatDebugResponse(
        student_id=student_id,
        steps=[s.to_dict() for s in steps],
        step_count=len(steps)
    )
```

```python
# app/predict/schemas/chat.py

from pydantic import BaseModel
from typing import Optional

class ChatDebugResponse(BaseModel):
    student_id: int
    steps: list[dict]
    step_count: int
```

### 2.3 前端debug开关

```jsx
// frontend/src/App.jsx

// 添加debug状态
const [showDebug, setShowDebug] = useState(false);
const [debugTrace, setDebugTrace] = useState(null);

// 切换debug模式
const toggleDebug = async () => {
    if (!showDebug) {
        // 获取trace
        try {
            const res = await fetch(`/api/v1/advice/${currentStudent}/debug`);
            const data = await res.json();
            setDebugTrace(data);
        } catch (e) {
            console.error("获取debug trace失败", e);
        }
    }
    setShowDebug(!showDebug);
};

// 渲染debug面板
{showDebug && debugTrace && (
    <div className="debug-panel">
        <h4>思考过程</h4>
        <div className="trace-list">
            {debugTrace.steps.map((step, i) => (
                <div key={i} className="trace-step">
                    <span className="trace-service">[{step.service}]</span>
                    <span className="trace-method">{step.method}</span>
                    <span className="trace-duration">{step.duration_ms}ms</span>
                    <div className="trace-detail">
                        <details>
                            <summary>输入/输出</summary>
                            <pre>输入: {step.input}</pre>
                            <pre>输出: {step.output}</pre>
                        </details>
                    </div>
                </div>
            ))}
        </div>
    </div>
)}
```

```css
/* debug面板样式 */
.debug-panel {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    max-height: 300px;
    overflow-y: auto;
    background: #1a1a2e;
    color: #eee;
    border-radius: 8px;
    padding: 12px;
    font-size: 12px;
    z-index: 1000;
}

.debug-panel h4 {
    margin: 0 0 8px 0;
    color: #667eea;
}

.trace-step {
    padding: 4px 0;
    border-bottom: 1px solid #333;
}

.trace-service {
    color: #f59e0b;
    font-weight: bold;
}

.trace-method {
    color: #10b981;
    margin-left: 8px;
}

.trace-duration {
    float: right;
    color: #999;
}

.trace-detail pre {
    margin: 4px 0;
    font-size: 10px;
    color: #ccc;
    white-space: pre-wrap;
}
```

---

## 三、架构图

```
用户请求
    │
    ▼
┌──────────────────────────────────────┐
│         ChatService.chat()           │
│                                      │
│  1. get_context()                    │
│     ├── @traceable PredictionService │
│     ├── @traceable PortraitService   │
│     ├── @traceable RiskService       │
│     └── @traceable SimulationService │
│                                      │
│  2. build_prompt()                   │
│     └── @traceable ChatService       │
│                                      │
│  3. _call_llm()                      │
│     └── @traceable ChatService       │
└──────────────┬───────────────────────┘
               │
    ┌──────────▼──────────┐
    │   TraceService       │
    │   (单例，全局收集)    │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  GET /debug 端点     │
    │  (返回trace列表)     │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  前端debug面板       │
    │  (可切换显示)       │
    └─────────────────────┘
```

---

## 四、文件结构

```
app/predict/
├── services/
│   ├── trace_service.py       # 新增：TraceService + 装饰器
│   ├── chat_service.py       # 改造：添加 @traceable
│   ├── prediction_service.py # 改造：添加 @traceable
│   ├── portrait_service.py   # 改造：添加 @traceable
│   └── risk_service.py       # 改造：添加 @traceable
├── schemas/
│   └── chat.py               # 改造：新增 ChatDebugResponse
└── api/v1/
    └── advice_router.py      # 改造：新增 /debug 端点

frontend/src/
├── App.jsx                   # 改造：添加debug开关和面板
└── App.css                   # 改造：添加debug面板样式
```

---

## 五、后端日志示例

```
[ChatService] get_context - 152.3ms
[PredictionService] predict_student_admission - 89.5ms
[PortraitService] analyze_student - 23.1ms
[RiskService] analyze_risk - 18.7ms
[SimulationService] simulate_score_increase - 45.2ms
[ChatService] build_prompt - 2.1ms
[ChatService] _call_llm - 1245.6ms
```

---

## 六、前端debug面板展示

```
┌─────────────────────────────────────┐
│ 思考过程                      [×]   │
├─────────────────────────────────────┤
│ [PredictionService] predict... 89ms │
│   输入: (1, 485)                    │
│   输出: {"predictions": {"冲刺": []..│
├─────────────────────────────────────┤
│ [PortraitService] analyze... 23ms   │
│   输入: (1,)                         │
│   输出: {"learning_type": "稳定型"..│
├─────────────────────────────────────┤
│ [RiskService] analyze... 19ms      │
│   输入: (1,)                         │
│   输出: {"risk_level": "中", ...}   │
├─────────────────────────────────────┤
│ [ChatService] _call_llm 1246ms      │
│   输入: "学生总分485分..."           │
│   输出: "根据你的情况..."           │
└─────────────────────────────────────┘
```

---

## 七、测试验证

```bash
# 运行测试脚本
python test_chat_debug.py

# 验证点：
# 1. simulation数据正确包含4条记录（+5/+10/+15/+20）
# 2. build_prompt正确包含simulation数据
# 3. LLM回答质量提升
```

---

## 八、自检清单

- [x] 问题分析：问非所答根因已定位
- [x] 修复方案：Prompt优化已明确
- [x] Trace机制：装饰器模式已设计
- [x] Debug端点：/debug 接口已设计
- [x] 前端debug面板：已设计UI
- [x] 文件结构：改动范围明确

---

**设计文档版本：** v2.1
**更新日期：** 2026-05-28
**状态：** 待实现