"""
Unified Four Great Novels Agent: Q&A + Journey to the West game.

Combines:
- PageIndex structural retrieval (keyword/chapter-based index)
- Milvus semantic search (vector embedding retrieval)
- JourneyEngine (Journey to the West interactive game)
"""

import json
import logging
import time
from typing import Iterator
from openai import OpenAI
from sqlalchemy.orm import Session

from app.services.rag_service import RAGService
from app.services.journey_engine import JourneyEngine
from app.core.milvus import MilvusService
from app.core.embedding import embed
from app.core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.core.llm_logger import log_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert on the Four Great Classical Novels of China: Romance of the Three Kingdoms (三国演义), Water Margin (水浒传), Dream of the Red Chamber (红楼梦), and Journey to the West (西游记).

You have two capabilities:

1. **Q&A Mode**: Answer questions about any of the four novels. Use search_novels (PageIndex keyword/chapter retrieval) to inspect available documents and their structure, then use get_chapter_content to fetch specific pages or line ranges. Use search_semantic (Milvus vector search) for fuzzy/conceptual queries. Always cite your sources (book name, chapter).

2. **Journey Game Mode**: The user can play an interactive Journey to the West text adventure. Use the journey tools (start_journey, get_journey_status, make_choice, get_knowledge_cards) to manage the game.

Decide which mode based on the user's intent. You can switch between modes freely within a conversation."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_novels",
            "description": "List available novels and their chapter/page structure. Optionally filter by doc_id. Returns document metadata and the hierarchical structure (page numbers, chapter hierarchy). Use the page numbers from the structure with get_chapter_content to retrieve full text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query to identify relevant documents"},
                    "doc_id": {"type": "string", "description": "Optional: limit to specific document ID from previous search results"},
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_semantic",
            "description": "Semantic vector search across Journey to the West content. Best for fuzzy/conceptual queries about characters, events, and themes. Returns matching passages with relevance scores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query for semantic search"},
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_chapter_content",
            "description": "Get the full content of specific pages or line ranges from a novel. Use page numbers or line ranges as returned by search_novels structure (e.g., '5-7' for pages 5 through 7, '3,8' for pages 3 and 8, '12' for a single page).",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "Document ID from search_novels results"},
                    "pages": {"type": "string", "description": "Page number or range, e.g., '5-7', '3,8', '12'. Use page numbers from search_novels structure output."},
                },
                "required": ["doc_id", "pages"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_journey",
            "description": "Start a new Journey to the West adventure game. Returns the opening chapter with choices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Client session ID for game state tracking"},
                },
                "required": ["session_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_journey_status",
            "description": "Get current game progress: chapter, karma, achievements, available choices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Client session ID"},
                },
                "required": ["session_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "make_choice",
            "description": "Make a choice in the current game chapter to advance the story.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Client session ID"},
                    "choice": {"type": "string", "description": "The user's choice text"},
                },
                "required": ["session_id", "choice"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_knowledge_cards",
            "description": "View all knowledge cards collected during the journey.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Client session ID"},
                },
                "required": ["session_id"]
            }
        }
    },
]

MAX_TOOL_CALLS = 5
MAX_HISTORY_MESSAGES = 60  # 每个会话最多保留的历史消息数

# 模块级对话历史存储: {session_id: [{role, content, ...}, ...]}
_conversations: dict[str, list[dict]] = {}


def _get_history(session_id: str) -> list[dict]:
    """获取指定会话的对话历史。"""
    return _conversations.get(session_id, [])


def _save_history(session_id: str, messages: list[dict]):
    """保存会话的对话历史（去掉 system prompt，限制最大消息数）。"""
    _conversations[session_id] = messages[-MAX_HISTORY_MESSAGES:]
    # 防止内存泄漏：超过 200 个会话时清理最旧的
    if len(_conversations) > 200:
        oldest = next(iter(_conversations))
        del _conversations[oldest]


class NovelsUnifiedService:
    """Unified Four Great Novels Agent: Q&A + Journey to the West game."""

    def __init__(self, db: Session, api_key: str = None, base_url: str = None):
        self.db = db
        self.rag = RAGService()
        self.milvus = MilvusService()
        self.journey = JourneyEngine(db)
        self.client = OpenAI(
            api_key=api_key or LLM_API_KEY,
            base_url=base_url or LLM_BASE_URL,
        )

    def _call_tool(self, name: str, arguments: dict) -> str:
        if name == "search_novels":
            return self._search_novels(arguments.get("query", ""), arguments.get("doc_id"))
        elif name == "search_semantic":
            return self._search_semantic(arguments.get("query", ""))
        elif name == "get_chapter_content":
            return self._get_chapter_content(arguments.get("doc_id", ""), arguments.get("pages", ""))
        elif name == "start_journey":
            return json.dumps(self.journey.start(arguments.get("session_id", "")), ensure_ascii=False)
        elif name == "get_journey_status":
            return json.dumps(self.journey.get_status(arguments.get("session_id", "")), ensure_ascii=False)
        elif name == "make_choice":
            return json.dumps(
                self.journey.choose(arguments.get("session_id", ""), arguments.get("choice", "")),
                ensure_ascii=False,
            )
        elif name == "get_knowledge_cards":
            status = self.journey.get_status(arguments.get("session_id", ""))
            return json.dumps(status.get("knowledge_cards", []), ensure_ascii=False)
        return json.dumps({"error": f"Unknown tool: {name}"})

    def _search_novels(self, query: str, doc_id: str = None) -> str:
        """PageIndex structural retrieval: list documents and return their structure."""
        docs = self.rag.client.list_documents()
        results = []
        target_docs = docs if not doc_id else [d for d in docs if d.get("doc_id") == doc_id]
        for doc in target_docs:
            try:
                structure = self.rag.client.get_document_structure(doc["doc_id"])
                structure_data = json.loads(structure) if isinstance(structure, str) else structure
            except Exception as e:
                structure_data = {"error": str(e)}
            result = {
                "doc_id": doc["doc_id"],
                "doc_name": doc.get("doc_name", ""),
                "structure": structure_data,
            }
            results.append(result)
        if not results:
            return json.dumps({"info": "No documents found", "query": query}, ensure_ascii=False)
        return json.dumps(results, ensure_ascii=False)

    def _search_semantic(self, query: str) -> str:
        """Milvus semantic vector search."""
        try:
            vector = embed(query)
            hits = self.milvus.search(vector, top_k=5)
            return json.dumps(hits, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
            return json.dumps({"error": f"Semantic search failed: {e}"}, ensure_ascii=False)

    def _get_chapter_content(self, doc_id: str, pages: str) -> str:
        """Get page content via PageIndex."""
        try:
            return self.rag.client.get_page_content(doc_id, pages)
        except Exception as e:
            return json.dumps({"error": f"Failed to get chapter content: {e}"}, ensure_ascii=False)

    def chat_stream(self, session_id: str, message: str, model: str = None) -> Iterator[str]:
        """Streaming chat with tool-calling loop. Yields SSE formatted events."""
        model = model or LLM_MODEL
        history = _get_history(session_id)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        tool_call_count = 0

        log_llm({
            "type": "user_message",
            "session_id": session_id,
            "content": message,
        })

        while tool_call_count < MAX_TOOL_CALLS:
            t0 = time.time()
            log_llm({
                "type": "llm_request",
                "model": model,
                "messages": messages,
                "tools": TOOLS,
                "stream": True,
                "session_id": session_id,
            })

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                stream=True,
                temperature=0.7,
            )

            assistant_content = []
            tool_calls_collected = []

            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    assistant_content.append(delta.content)
                    yield f"data: {json.dumps({'type': 'text', 'content': delta.content}, ensure_ascii=False)}\n\n"
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        while len(tool_calls_collected) <= tc.index:
                            tool_calls_collected.append(None)
                        if tool_calls_collected[tc.index] is None:
                            tool_calls_collected[tc.index] = {"id": "", "function": {"name": "", "arguments": ""}}
                        if tc.id:
                            tool_calls_collected[tc.index]["id"] = tc.id
                        if tc.function.name:
                            tool_calls_collected[tc.index]["function"]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_collected[tc.index]["function"]["arguments"] += tc.function.arguments

            valid_tool_calls = [tc for tc in tool_calls_collected if tc and tc.get("function", {}).get("name")]

            full_text = "".join(assistant_content)
            log_llm({
                "type": "llm_response",
                "model": model,
                "content": full_text,
                "tool_calls": [
                    {"id": tc["id"], "function": tc["function"]}
                    for tc in valid_tool_calls
                ],
                "finish_reason": "tool_calls" if valid_tool_calls else "stop",
                "latency_ms": int((time.time() - t0) * 1000),
                "session_id": session_id,
            })

            if not valid_tool_calls:
                if assistant_content:
                    messages.append({"role": "assistant", "content": full_text})
                break

            tool_call_count += 1
            logger.info(
                f"[NovelsAgent] Tool call #{tool_call_count}: "
                f"{[tc['function']['name'] for tc in valid_tool_calls]}"
            )

            for tc in valid_tool_calls:
                log_llm({
                    "type": "tool_call",
                    "tool": tc["function"]["name"],
                    "args": tc["function"]["arguments"],
                    "session_id": session_id,
                })
                yield (
                    f"data: {json.dumps({'type': 'tool_call', 'tool': tc['function']['name'], 'args': tc['function']['arguments']}, ensure_ascii=False)}\n\n"
                )

            tool_results = []
            for tc in valid_tool_calls:
                func_name = tc["function"]["name"]
                func_args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                t_tool = time.time()
                result = self._call_tool(func_name, func_args)
                tool_results.append({"tool_call_id": tc["id"], "result": result})
                log_llm({
                    "type": "tool_result",
                    "tool": func_name,
                    "summary": result[:500],
                    "ok": True,
                    "duration_ms": int((time.time() - t_tool) * 1000),
                    "session_id": session_id,
                })
                yield (
                    f"data: {json.dumps({'type': 'tool_result', 'tool': func_name, 'result': result[:500]}, ensure_ascii=False)}\n\n"
                )

            assistant_msg = {"role": "assistant"}
            if assistant_content:
                assistant_msg["content"] = "".join(assistant_content)
            if valid_tool_calls:
                assistant_msg["tool_calls"] = [
                    {"id": tc["id"], "type": "function", "function": tc["function"]}
                    for tc in valid_tool_calls
                ]
            messages.append(assistant_msg)

            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": tr["result"],
                })

        if tool_call_count >= MAX_TOOL_CALLS:
            messages.append({
                "role": "user",
                "content": "You have enough information. Summarize your findings for the user.",
            })
            t0 = time.time()
            log_llm({
                "type": "llm_request",
                "model": model,
                "messages": messages,
                "stream": True,
                "session_id": session_id,
            })

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.7,
            )
            final_content = []
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    final_content.append(delta.content)
                    yield f"data: {json.dumps({'type': 'text', 'content': delta.content}, ensure_ascii=False)}\n\n"

            log_llm({
                "type": "llm_response",
                "model": model,
                "content": "".join(final_content),
                "finish_reason": "stop",
                "latency_ms": int((time.time() - t0) * 1000),
                "session_id": session_id,
            })

        # 保存本轮完整对话历史（去掉 system prompt），供下一轮继续使用
        _save_history(session_id, messages[1:])

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
