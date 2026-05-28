# AI 数学 Tutor

基于贝叶斯掌握度追踪和确定性验证的自适应 AI 辅导系统。

## 学习循环

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│          │     │          │     │          │     │          │     │          │     │          │
│  推荐    │────▶│  生成    │────▶│  作答    │────▶│  验证    │────▶│ LLM反馈  │────▶│ 更新掌握 │
│          │     │          │     │          │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
      ▲                                                                                    │
      │                    recommender.record(outcome)                                    │
      │                    mastery.variance → 平局裁决                                     │
      │                                                                                   │
      └───────────────────────────────────────────────────────────────────────────────────┘
                                   next_question()
```

1. **推荐** — 三层策略从掌握度状态中选择知识点 + 难度
2. **生成** — SymPy 在指定难度下随机生成可解题目
3. **作答** — 学生提交自由文本数学表达式
4. **验证** — 符号比较加数值回退，永不崩溃
5. **LLM 反馈** — LLM 生成解析、提示、鼓励（可选，失败不影响核心）
6. **更新掌握度** — Beta-Binomial 后验更新，推荐器记录结果

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                      Streamlit UI                        │
│               ui/streamlit_app.py (单页)                  │
└──────────────────────┬───────────────────────────────────┘
                       │ TutorSession
┌──────────────────────┴───────────────────────────────────┐
│                    session.py                            │
│                    会话编排                               │
└────┬─────────────────┬─────────────────┬────────────────┘
     │                 │                 │
┌────▼────┐      ┌─────▼──────┐    ┌─────▼──────┐    ┌─────▼──────┐
│ engine  │      │  mastery   │    │ recommender│    │tutor_agent │
│  .py    │      │   .py      │    │    .py     │    │    .py     │
│         │      │            │    │            │    │            │
│ 15 个   │      │ Beta(3,3)  │    │ 三层选择    │    │ LLM 教学   │
│ 模板    │      │ 先验       │    │            │    │ 反馈       │
│         │      │            │    │            │    │            │
│ SymPy   │      │ 内存 dict  │    │ 挫折保护    │    │ 失败安全   │
│ 安全层  │      │            │    │            │    │ 可选       │
└─────────┘      └────────────┘    └────────────┘    └────────────┘
 5 个知识点         逐 topic α/β       确定性             仅教学
 可验证              + 方差           可解释             建议
```

## 快速开始

```bash
pip install streamlit sympy python-dotenv
streamlit run ui/streamlit_app.py --server.headless true
# → http://localhost:8501
```

可选 LLM 教学反馈 — 在项目根目录创建 `.env`：

```
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1    # 或 DashScope / Ollama / vLLM
LLM_MODEL=gpt-4o-mini                        # 或 qwen-plus、llama3 等
```

如果不存在 `.env`，系统正常运行，只是没有 AI 导师点评。

运行测试：

```bash
python -m pytest tests/ -q     # 253 passed
```

## 项目结构

```
ai-tutor/
├── app/
│   ├── engine.py          # SymPy 出题引擎（15 个模板）
│   ├── mastery.py         # Beta-Binomial 掌握度追踪
│   ├── recommender.py     # 三层知识点 + 难度选择器
│   ├── session.py         # 教学循环编排
│   ├── tutor_agent.py     # LLM 教学反馈（可选）
│   ├── main.py            # FastAPI 应用（5 个端点）
│   └── schemas.py         # Pydantic v2 请求/响应模型
├── ui/
│   └── streamlit_app.py   # Streamlit 单页 UI
├── tests/                 # 253 个测试
├── ARCHITECTURE.md        # 完整架构文档
├── DEMO_SCRIPT.md         # 可运行的演示脚本
├── KNOWN_LIMITATIONS.md   # 已知限制与未来方向
└── LIMITATIONS.md         # 当前限制与修复路径
```

## 当前限制

**难度启发式估计** — easy/medium/hard 标签按模板静态分配，未经学生数据校准。跨知识点难度不可比较。

**无大规模校准** — 模板参数手工选取，未经真实学生试验调优。

**知识点图谱有限** — 5 个知识点，最大深度 2。每个知识点独立 Beta 分布，无跨知识点知识迁移。

**无长期记忆持久化** — 所有状态在内存中。刷新或重启丢失全部进度。（修复方案：`MasteryStore.save/load` JSON 文件，无需数据库。）

**仅支持单变量** — 所有题目使用 `x`。无多元微积分、几何、文字题。

**答案格式敏感** — 二次方程求根要求逗号分隔（`-1,-4`）。等价形式如 `x=-1, x=-4` 不被识别。

详见 [LIMITATIONS.md](LIMITATIONS.md) 了解修复路径。

## 技术栈

| 层 | 选型 |
|-------|--------|
| 数学引擎 | SymPy（符号生成 + 验证） |
| 掌握度模型 | Beta-Binomial 贝叶斯更新 |
| 题目推荐 | 三层确定性策略 |
| LLM 辅导 | OpenAI 兼容 API（可选，qwen-plus / gpt-4o-mini） |
| API | FastAPI（5 个端点）+ Streamlit（直接 Python 调用） |
| UI | Streamlit |
| 存储 | 内存 dict |
| 测试 | pytest（253 个测试） |
