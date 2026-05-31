import os
import json
import logging
from typing import Iterator
from openai import OpenAI
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个四大名著专家，精通《三国演义》、《水浒传》、《红楼梦》、《西游记》。

当你需要回答问题时：
1. 先调用 get_all_documents 获取文档列表
2. 调用 get_document_structure 查看书籍结构
3. 调用 get_page_content 获取相关章节内容
4. 基于检索内容回答，不要编造

回答时标注内容来源（书名、章节）。"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_all_documents",
            "description": "获取四大名著列表，返回文档ID、名称、描述",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_structure",
            "description": "获取指定书籍的章节结构，用于定位相关内容",
            "parameters": {
                "type": "object",
                "properties": {"doc_id": {"type": "string", "description": "文档ID"}},
                "required": ["doc_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": "获取指定行号范围的内容，格式如 '100-150'",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "文档ID"},
                    "pages": {"type": "string", "description": "行号范围，如 '100-150' 或 '100,105'"}
                },
                "required": ["doc_id", "pages"]
            }
        }
    }
]

MAX_TOOL_CALLS = 3

class AgentService:
    """Agent 服务：LLM 调用 + Tool Calling Loop + SSE 流式输出"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.rag = RAGService()
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_API_BASE_URL") or "https://api.openai.com/v1"
        )

    def _call_tool(self, name: str, arguments: dict) -> str:
        """执行工具调用"""
        if name == "get_all_documents":
            return self.rag.get_all_documents()
        elif name == "get_document_structure":
            return self.rag.get_document_structure(arguments.get("doc_id", ""))
        elif name == "get_page_content":
            return self.rag.get_page_content(
                arguments.get("doc_id", ""),
                arguments.get("pages", "")
            )
        return json.dumps({"error": f"Unknown tool: {name}"})

    def chat_stream(self, question: str, model: str = None) -> Iterator[str]:
        """流式问答，参考 code.py 的 agent loop"""
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]

        tool_call_count = 0

        while tool_call_count < MAX_TOOL_CALLS:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                stream=True,
                temperature=0.7
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
            if not valid_tool_calls:
                break

            logger.info(f"[Agent] 第 {tool_call_count + 1} 次调用工具: {[tc['function']['name'] for tc in valid_tool_calls]}")

            tool_results = []
            for tc in valid_tool_calls:
                func_name = tc["function"]["name"]
                func_args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                logger.info(f"[Agent] 调用工具 {func_name}, 参数: {func_args}")
                result = self._call_tool(func_name, func_args)
                logger.info(f"[Agent] 工具 {func_name} 返回内容:\n{result[:500]}...")  # 只打印前500字符
                tool_results.append({
                    "tool_call_id": tc["id"],
                    "result": result
                })

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
                    "content": tr["result"]
                })

            tool_call_count += 1

        if tool_call_count >= MAX_TOOL_CALLS:
            messages.append({
                "role": "user",
                "content": "你已获取足够信息，请基于以上内容总结回答用户问题。"
            })
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.7
            )
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'type': 'text', 'content': delta.content}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"