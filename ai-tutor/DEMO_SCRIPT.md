# AI Tutor — 演示脚本

## 环境准备

```bash
cd ai-tutor
pip install pytest sympy python-dotenv
# 或 uv sync
```

## Demo 1: 确定性引擎演示

```python
from app.engine import QuestionEngine, safe_compare

# 固定 seed → 可复现
engine = QuestionEngine(seed=42)

# 生成 5 个知识点的简单题
for topic in engine.TOPICS:
    q = engine.generate(topic, "easy")
    print(f"[{topic}] {q.question_text}")
    print(f"  答案: {q.answer}")
    print()

# 输出示例:
# [linear_equation] Solve: $3x = -30$
#   答案: -10
# [quadratic_equation] Solve: $x^2 = 9$
#   答案: -3,3
# [factoring] Factor: $5*x + 45$
#   答案: 5*(x + 9)
# [derivative] Find $d/dx$ of $x^{3}$
#   答案: 3*x**2
# [integral] Integrate: $\int x**4 \, dx$
#   答案: x**5/5

# 验证答案
q = engine.generate("linear_equation", "medium")
print(f"题目: {q.question_text}")
print(f"标准答案: {q.answer}")
print(f"学生答 '3': {safe_compare('3', q.answer)}")
print(f"学生答 '5': {safe_compare('5', q.answer)}")
```

## Demo 2: 掌握度追踪

```python
from app.mastery import MasteryStore

store = MasteryStore()

# 初始状态
state = store.get("linear_equation")
print(f"初始 mastery: {state.mastery:.2f}")   # 0.50
print(f"初始 variance: {state.variance:.4f}") # ~0.0357

# 连续答对 5 题
for i in range(5):
    state = store.update("linear_equation", True)
    print(f"第{i+1}次答对: mastery={state.mastery:.3f}, variance={state.variance:.4f}")

# 输出:
# 第1次答对: mastery=0.571, variance=0.0306
# 第2次答对: mastery=0.625, variance=0.0250
# 第3次答对: mastery=0.667, variance=0.0202
# 第4次答对: mastery=0.700, variance=0.0164
# 第5次答对: mastery=0.727, variance=0.0135

# 连续答错的效果
store2 = MasteryStore()
for i in range(3):
    state = store2.update("quadratic_equation", False)
    print(f"第{i+1}次答错: mastery={state.mastery:.3f}")
# mastery 从 0.5 降到 0.333
```

## Demo 3: 推荐策略

```python
from app.mastery import MasteryStore
from app.recommender import Recommender

store = MasteryStore()
rec = Recommender(store)

# 场景1: 初始状态 → 只有 linear_equation 无前置依赖
r = rec.recommend()
print(f"初始推荐: {r.topic} / {r.difficulty}")
print(f"原因: {r.reason}")
# 输出: 初始推荐: linear_equation / medium
#       原因: tier=challenge; blocked=['quadratic_equation', 'factoring', 'derivative', 'integral']

# 场景2: linear_equation 掌握后 → 解锁更多 topic
for _ in range(10):
    store.update("linear_equation", True)
r = rec.recommend()
print(f"\n掌握线性方程后: {r.topic} / {r.difficulty}")
print(f"原因: {r.reason}")
# 不再有 blocked topics

# 场景3: 挫折保护
for _ in range(3):
    rec.record("quadratic_equation", False)
r = rec.recommend()
print(f"\n连续3次错误后: {r.topic} / {r.difficulty}")
print(f"原因: {r.reason}")
# topic 切换 + 难度降低
```

## Demo 4: 完整会话模拟

```python
from app.engine import QuestionEngine
from app.mastery import MasteryStore
from app.recommender import Recommender
from app.session import TutorSession
from app.tutor_agent import TutorAgent

engine = QuestionEngine(seed=42)
store = MasteryStore()
rec = Recommender(store)
agent = TutorAgent(mock=True)  # mock 模式，无需 API key
session = TutorSession(engine, store, rec, tutor_agent=agent)

# 模拟一个学生：前5题全对，后5题全错
print("=" * 50)
print("模拟教学会话")
print("=" * 50)

for i in range(10):
    q = session.next_question()
    # 前5题答对，后5题答错
    answer = q.answer if i < 5 else "wrong_answer"
    fb = session.submit_answer(answer)

    status = "✓" if fb.is_correct else "✗"
    print(f"\n第{i+1}题 {status}")
    print(f"  Topic: {q.topic} | 难度: {q.difficulty}")
    print(f"  题目: {q.question_text}")
    print(f"  你的答案: {answer}")
    if not fb.is_correct:
        print(f"  正确答案: {fb.correct_answer}")

# 查看最终进度
progress = session.get_progress()
print(f"\n{'='*50}")
print(f"总结:")
print(f"  总题数: {progress.total_questions}")
print(f"  正确数: {progress.correct_count}")
print(f"  正确率: {progress.accuracy:.0%}")
print(f"  当前连对: {progress.correct_streak}")
print(f"  当前连错: {progress.wrong_streak}")
print(f"\n掌握度:")
for s in progress.mastery_states:
    bar = "█" * int(s.mastery * 10) + "░" * (10 - int(s.mastery * 10))
    print(f"  {s.topic_id:20s} [{bar}] {s.mastery:.2f}")
```

预期输出显示：
- 前 5 题正确 → mastery 上升
- 后 5 题错误 → 挫折保护触发，难度降低
- 最终 mastery 反映答题表现

## Demo 5: 确定性验证

```python
from app.engine import QuestionEngine
from app.mastery import MasteryStore
from app.recommender import Recommender
from app.session import TutorSession

def run_session(seed):
    engine = QuestionEngine(seed=seed)
    store = MasteryStore()
    rec = Recommender(store)
    session = TutorSession(engine, store, rec)

    for _ in range(20):
        q = session.next_question()
        session.submit_answer(q.answer)  # 全对
    return session.get_progress()

# 两次运行 → 完全相同的结果
p1 = run_session(42)
p2 = run_session(42)

assert p1.total_questions == p2.total_questions
assert p1.accuracy == p2.accuracy
assert p1.correct_streak == p2.correct_streak

print("两次运行结果完全一致 ✓")
print(f"总题数: {p1.total_questions}")
print(f"正确率: {p1.accuracy:.0%}")
print(f"连对: {p1.correct_streak}")

# 不同 seed → 不同结果
p3 = run_session(99)
print(f"\n不同 seed 的总题数: {p3.total_questions}")
print(f"结果不同: {p1.total_questions != p3.total_questions}")
```

## Demo 6: LLM 教学反馈

```python
from app.engine import QuestionEngine
from app.mastery import MasteryStore
from app.recommender import Recommender
from app.session import TutorSession
from app.tutor_agent import TutorAgent

agent = TutorAgent(mock=True)
engine = QuestionEngine(seed=42)
store = MasteryStore()
rec = Recommender(store)
session = TutorSession(engine, store, rec, tutor_agent=agent)

# 答对一题
q = session.next_question()
fb = session.submit_answer(q.answer)
print(f"正确: {fb.is_correct}")
print(f"解析: {fb.tutor_response.explanation}")
print(f"提示: {fb.tutor_response.hint}")
print(f"鼓励: {fb.tutor_response.encouragement}")

# 答错一题
q = session.next_question()
fb = session.submit_answer("wrong_answer")
print(f"\n正确: {fb.is_correct}")
print(f"解析: {fb.tutor_response.explanation}")
print(f"提示: {fb.tutor_response.hint}")
print(f"鼓励: {fb.tutor_response.encouragement}")

# 不配置 agent → 无反馈
session2 = TutorSession(engine, store, rec)  # 无 tutor_agent
q = session2.next_question()
fb = session2.submit_answer(q.answer)
print(f"\ntutor_response 为 None: {fb.tutor_response is None}")
```

## 运行所有测试

```bash
cd ai-tutor
python -m pytest tests/ -v

# 预期: 253 passed
```
