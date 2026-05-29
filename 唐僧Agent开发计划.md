# 🧘 唐僧 Agent 开发计划

## 项目背景

在现有 SIMS-NEXT 项目（FastAPI + SQLAlchemy 2.0 + Pydantic v2）中新增一个"唐僧 Agent"模块，实现基于 RAG 的角色扮演对话功能。

### 核心流程

```
用户消息 → LLM 分析 personality/emotion/tone → Embedding → Milvus 向量检索
→ MySQL 查对话详情 → 组装 Prompt → LLM 生成唐僧回复 → 返回给用户
```

---

## 现状

| 项目 | 内容 |
|------|------|
| MySQL 表 | `xiyouji.xiyouji_persona` — 已存入 409 条对话记录，含 `personality`/`emotion`/`tone` JSON 字段 |
| Milvus 集合 | `xiyouji_persona` — 1024 维向量，含 `embedding`、`speaker`、`embedding_text`、`metadata` |
| LLM 选型 | OpenAI 兼容 API |
| 交互方式 | REST API 端点 (`POST /api/v1/xiyouji/chat`) |
| 项目框架 | FastAPI + SQLAlchemy 2.0 + Pydantic v2，分层架构：路由 → 服务 → 仓库 → 模型 |

### MySQL `xiyouji_persona` 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | bigint PK | 主键，关联 Milvus |
| `book_name` | varchar(255) | 书名，默认"西游记" |
| `chapter` | int | 章节号 |
| `chapter_title` | text | 章节标题 |
| `chunk_index` | int | 段落索引 |
| `speaker` | varchar(32) | 说话人 |
| `scene_summary` | text | 场景描述 |
| `content` | longtext | 对话原文 |
| `embedding_text` | longtext | 用于生成向量的文本 |
| `personality` | json | 性格标签 |
| `emotion` | json | 情绪标签 |
| `tone` | json | 语气标签 |
| `topic` | json | 话题标签 |
| `created_at` | timestamp | 创建时间 |

### MySQL `xiyouji_conversation` 表结构（对话历史）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | bigint PK | 主键 |
| `session_id` | varchar(64) | 会话 ID（客户端生成） |
| `role` | varchar(16) | 角色：`user` / `assistant` |
| `content` | text | 对话内容 |
| `personality` | varchar(64) | 本轮唐僧性格标签 |
| `emotion` | varchar(64) | 本轮唐僧情绪标签 |
| `tone` | varchar(64) | 本轮唐僧语气标签 |
| `created_at` | timestamp | 创建时间 |

**说明**：
- 按 `session_id` + `created_at` 查询可获取完整对话历史
- `personality`/`emotion`/`tone` 记录本轮分析结果，用于后续分析或审计
- 定期清理：可按业务需求定期删除过期的 session 记录

### Milvus `xiyouji_persona` 集合结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | varchar(64) PK | 主键，等于 MySQL `id` 的字符串形式 |
| `chapter` | int64 | 章节号 |
| `speaker` | varchar(64) | 说话人 |
| `embedding_text` | varchar(4096) | 用于生成向量的文本 |
| `metadata` | JSON | 元数据 |
| `embedding` | float_vector(1024) | 1024 维向量嵌入 |

---

## 执行步骤

### 步骤 1 — 安装依赖

```bash
uv add openai pymilvus
```

安装后 `pyproject.toml` 的 `dependencies` 会新增 `openai` 和 `pymilvus`。

---

### 步骤 2 — 配置环境变量

**`.env`** 新增：
```env
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.minimaxi.com/v1
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=xiyouji_persona
```

**修改 `app/core/config.py`**，新增读取：
| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥（用于 MiniMax 兼容 API） |
| `OPENAI_BASE_URL` | API 端点（默认 `https://api.minimaxi.com/v1`） |
| `MILVUS_HOST` | Milvus 主机 |
| `MILVUS_PORT` | Milvus 端口 |
| `MILVUS_COLLECTION` | Milvus collection 名称 |

---

### 步骤 3 — 新建 `app/core/llm.py`

LLM 客户端封装，两个核心方法：

| 方法 | 用途 | 使用模型 |
|------|------|---------|
| `chat(messages)` → `str` | 分析用户问题 + 生成唐僧回复 | MiniMax API（OpenAI 兼容） |
| `embed(text)` → `list[float]` | 文本转向量（Milvus 检索用）| 本地模型 `bge-large-zh-v1.5`（D:\model\BAbge-large-zh-v1.5） |

**说明**：
- `chat()` 调用 MiniMax API（`OPENAI_API_KEY` + `OPENAI_BASE_URL`）
- `embed()` 调用本地 embedding 模型，不走 API

---

### 步骤 4 — 新建 `app/core/milvus.py`

Milvus 连接和搜索封装：

```python
class MilvusService:
    def __init__(self):          # 连接 Milvus
    def search(query_vector, top_k=5) -> list[dict]:   # 向量搜索
    # 返回 [{id, chapter, speaker, embedding_text, distance}, ...]
```

---

### 步骤 5 — 新建 `app/models/xiyouji.py`

SQLAlchemy ORM 模型，映射 MySQL `sims` 库中的两张表：

```python
class XiyoujiPersona(Base):
    __tablename__ = "xiyouji_persona"
    __table_args__ = {"schema": "sims"}

class XiyoujiConversation(Base):
    __tablename__ = "xiyouji_conversation"
    __table_args__ = {"schema": "sims"}
```

---

### 步骤 6 — 新建 `app/schemas/xiyouji.py`

Pydantic v2 请求/响应模式：

```python
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID（客户端生成）")
    message: str = Field(..., description="用户消息")
    history: list[Message] | None = Field(default=None, description="历史对话（可选）")

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatResponse(BaseModel):
    reply: str
    personality: str | None = None
    emotion: str | None = None
    tone: str | None = None
```

---

### 步骤 7 — 新建 `app/repositories/xiyouji_repository.py`

MySQL 数据访问封装：

| 方法 | 说明 |
|------|------|
| `get_by_ids(ids: list[int])` | 按主键批量查询 xiyouji_persona 完整记录 |
| `get_conversation_history(session_id, limit=20)` | 查询指定 session 的对话历史，按时间升序 |
| `save_message(session_id, role, content, personality, emotion, tone)` | 保存单条对话到 xiyouji_conversation 表 |

---

### 步骤 8 — 新建 `app/services/xiyouji_service.py`（核心逻辑）

**RAG Pipeline 详细流程：**

```
用户消息 "师父，前面有妖怪吗？"
  │
  ▼
① LLM 分析 → 判断该场景下唐僧应表现出的 personality / emotion / tone
   ↓ 输出结构化 JSON
   {"personality": "慈悲", "emotion": "忧虑", "tone": "温和"}
  │
  ▼
② 构建查询文本 → "慈悲 忧虑 温和 唐僧"
  │
  ▼
③ Embedding API → 转为 1024 维向量
  │
  ▼
④ Milvus 搜索 → 在 xiyouji_persona 集合中召回 top-5
  │
  ▼
⑤ MySQL 查详情 → 用 Milvus 返回的 id 查 xiyouji_persona 表获取 content
  │
  ▼
⑥ 组装 Prompt（包含历史对话）:
     System: "你是唐僧，以下是你以往类似情景中的对话示例，请模仿其语气回复"
     History: [用户: xxx, 唐僧: yyy, ...]  ← 从 xiyouji_conversation 表获取
     Example 1: (content from RAG)
     Example 2: (content from RAG)
     ...
     User: "师父，前面有妖怪吗？"
  │
  ▼
⑦ LLM Chat → 生成唐僧风格回复
  │
  ▼
⑧ 保存对话到 xiyouji_conversation 表（role=user, role=assistant）
  │
  ▼
⑨ 返回 ChatResponse
```

**两步 Prompt 设计：**

```python
# 第一步：分析用户消息，判断语气/情绪/性格
ANALYSIS_PROMPT = """分析用户消息，判断唐僧应使用的回话风格。
返回 JSON 格式：
{
  "personality": "慈悲/严厉/智慧/...",
  "emotion": "平和/忧虑/愤怒/欣慰/...",
  "tone": "温和/严肃/急切/..."
}"""

# 第二步：RAG 检索后，组装带示例的对话 prompt
CHAT_PROMPT = """你是唐僧（唐三藏），一位从大唐前往西天取经的高僧。

以下是你以往在类似情景中的对话示例，请模仿其语气、情绪和表达方式：

{examples}

用户对你说：{user_message}

请以唐僧的身份回复，保持上述示例的风格。不要提及"作为AI"或"作为模型"。"""
```

---

### 步骤 9 — 新建 `app/api/v1/xiyouji.py`

```python
router = APIRouter(prefix="/xiyouji", tags=["唐僧Agent"])

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, service: XiyoujiService = Depends(get_xiyouji_service)):
    """
    发送消息给唐僧，获取回复。

    - **session_id**: 会话 ID，用于关联对话历史
    - **message**: 用户消息
    - **history**: 可选的历史对话列表（如果传入则优先使用服务端存储的历史）
    """
    return service.chat(request.session_id, request.message, request.history)
```

---

### 步骤 10 — 在 `app/main.py` 注册路由

```python
from app.api.v1.xiyouji import router as xiyouji_router
app.include_router(xiyouji_router, prefix="/api/v1")
```

---

## 完整文件清单

| # | 文件 | 操作 | 预估行数 |
|---|------|------|---------|
| 1 | `app/core/llm.py` | 新建 | ~30 行 |
| 2 | `app/core/milvus.py` | 新建 | ~25 行 |
| 3 | `app/models/xiyouji.py` | 新建 | ~50 行（含两个模型） |
| 4 | `app/schemas/xiyouji.py` | 新建 | ~25 行 |
| 5 | `app/repositories/xiyouji_repository.py` | 新建 | ~40 行 |
| 6 | `app/services/xiyouji_service.py` | 新建 | ~100 行（核心） |
| 7 | `app/api/v1/xiyouji.py` | 新建 | ~30 行 |
| 8 | `app/core/config.py` | 修改 | +4 行 |
| 9 | `app/main.py` | 修改 | +2 行 |
| 10 | `.env` | 修改 | +4 行 |

## SQL 建表语句

```sql
CREATE TABLE IF NOT EXISTS `sims`.`xiyouji_conversation` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `session_id` VARCHAR(64) NOT NULL,
  `role` VARCHAR(16) NOT NULL COMMENT 'user | assistant',
  `content` TEXT NOT NULL,
  `personality` VARCHAR(64) DEFAULT NULL,
  `emotion` VARCHAR(64) DEFAULT NULL,
  `tone` VARCHAR(64) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_session_id` (`session_id`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 关键技术决策

### 1. 两步 LLM 调用
先用 MiniMax API 分析情绪/语气/性格（输出 JSON），检索后再用同一 MiniMax API 生成回复。两步分离的好处是：分析结果可作为 debug 输出，检索词可人工干预。

**可选优化**：若延迟敏感，可合并为一次调用——在单个 prompt 中同时输出 JSON 分析和回复，但会增加 prompt 长度和成本。

### 2. Milvus 查询向量
用本地模型 `bge-large-zh-v1.5`（1024 维，与现有 Milvus 集合一致）生成向量，进行相似度检索。将分析出的 `personality + emotion + tone + "唐僧"` 拼接后做 embedding 搜索。

### 3. 备用逻辑
若 Milvus 检索结果中 `speaker` 不是唐僧，按距离排序后优先取 speaker=唐僧的结果，或取全局最相似结果。

### 4. 降级策略
- Milvus 不可用时：跳过 RAG 检索，直接用 LLM 生成回复（不带示例增强）
- Embedding 服务不可用时：返回错误或使用默认 personality/emotion/tone

### 5. Milvus 配置
需在 `.env` 中配置：
```
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=xiyouji_persona
```

### 6. 对话历史存储策略
使用 MySQL `xiyouji_conversation` 表存储对话历史，支持真正的多轮对话：

1. **每次对话**：先读取 `session_id` 的历史记录 → 拼入 Prompt → LLM 生成回复 → 分别保存用户消息和 Agent 回复
2. **历史窗口**：默认查询最近 20 条记录（可配置），避免 Prompt 过长
3. **字段记录**：保存本轮的 `personality`/`emotion`/`tone` 分析结果，便于后续分析唐僧的情绪变化
4. **清理策略**：可按业务需求定期删除过期 session（如保留 30 天）

### 7. 两步 LLM 调用的 JSON 解析容错

第一步 LLM 分析输出的 JSON 可能格式不完全匹配，代码需处理：
- 多余空格、换行
- 缺少必要字段
- 额外的注释或说明文字

解析失败时使用默认标签：`personality="慈悲", emotion="平和", tone="温和"`

