import json
import re
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.core.llm import chat, embed
from app.core.milvus import MilvusService
from app.repositories.xiyouji_repository import XiyoujiRepository
from app.schemas.xiyouji import Message

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """分析用户消息，判断唐僧应使用的回话风格。
返回 JSON 格式：
{
  "personality": "慈悲/严厉/智慧/...",
  "emotion": "平和/忧虑/愤怒/欣慰/...",
  "tone": "温和/严肃/急切/..."
}"""

JOURNEY_KEYWORDS = ["加入取经队伍", "开始取经", "我要取经", "成为徒弟", "取经游戏"]
JOURNEY_EXIT_KEYWORDS = ["退出游戏", "退出取经", "不玩了", "结束游戏", "退出"]


def parse_llm_json(raw: str) -> dict:
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {"personality": "慈悲", "emotion": "平和", "tone": "温和"}


def extract_think_reply(text: str) -> tuple[str, str]:
    """从LLM回复中提取思考过程和正式回复"""
    think_match = re.search(r"<think>\s*(.*?)\s*</think>", text, re.DOTALL)
    if think_match:
        think = think_match.group(1).strip()
        # reply 在 </think> 之后
        reply = text[think_match.end():].strip()
        # 去掉可能的 markdown 代码块标记
        reply = re.sub(r"^```(?:markdown)?\s*\n", "", reply)
        reply = re.sub(r"\n```$", "", reply)
        return think, reply
    return "", text


class XiyoujiService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = XiyoujiRepository(db)
        self.milvus = MilvusService()

    def is_journey_intent(self, message: str) -> bool:
        for keyword in JOURNEY_KEYWORDS:
            if keyword in message:
                return True
        return False

    def chat(
        self, session_id: str, message: str, history: Optional[list[Message]] = None
    ) -> dict:
        # ① LLM 分析 personality/emotion/tone
        analysis_raw = chat([
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": message},
        ])
        analysis = parse_llm_json(analysis_raw)
        personality = analysis.get("personality", "慈悲")
        emotion = analysis.get("emotion", "平和")
        tone = analysis.get("tone", "温和")

        # ② 构建查询文本 → Embedding → Milvus 搜索
        query_text = f"{personality} {emotion} {tone} 唐僧"
        query_vector = embed(query_text)
        milvus_results = self.milvus.search(query_vector, top_k=5)

        # ③ 直接从 Milvus 结果获取示例
        if milvus_results:
            # 优先取 speaker=唐僧的，按距离排序
            sorted_hits = sorted(milvus_results, key=lambda h: h["distance"])
            tang_hits = [h for h in sorted_hits if h.get("speaker") == "唐僧"]
            other_hits = [h for h in sorted_hits if h.get("speaker") != "唐僧"]
            ordered_hits = tang_hits + other_hits

            examples = []
            for h in ordered_hits[:3]:  # 最多3条示例
                speaker = h.get("speaker", "未知")
                text = h.get("embedding_text", "")
                distance = h.get("distance", 0.0)
                if text:
                    # 截断过长的文本，保留前200字
                    if len(text) > 200:
                        text = text[:200] + "..."
                    examples.append({
                        "speaker": speaker,
                        "text": text,
                        "score": round(distance, 4)
                    })
        else:
            examples = []

        examples_text = "\n\n".join(
            f"[{ex['speaker']}] {ex['text']}" for ex in examples
        ) if examples else "（无相关示例）"

        # ④ 组装历史对话
        if history:
            history_lines = []
            for msg in history:
                role_label = "用户" if msg.role == "user" else "唐僧"
                history_lines.append(f"{role_label}：{msg.content}")
            history_text = "\n".join(history_lines) + "\n"
        else:
            stored_history = self.repo.get_conversation_history(session_id, limit=20)
            history_lines = []
            for msg in stored_history:
                role_label = "用户" if msg.role == "user" else "唐僧"
                history_lines.append(f"{role_label}：{msg.content}")
            history_text = "\n".join(history_lines) + "\n" if history_lines else ""

        # ⑤ 简化 Prompt
        system_content = f"""你扮演的是唐僧（唐三藏），一位慈悲为怀、坚守佛法的取经人。

以下是你以往类似情景中的对话示例，请模仿其语气、情绪和表达方式：
{examples_text}

历史对话：
{history_text if history_text else "（无历史对话）"}

现在用户对你说：{message} ，你的任务是根据用户的消息，生成符合唐僧回话风格的回复。

## 回答要求
1. 始终保持唐僧的人设和说话风格
2. 可以结合检索到的西游记知识进行回答
3. 回答应该体现唐僧的慈悲、坚定和善良
4. 文言文与白话文结合，符合古人说话习惯
5. 回复字数不要超过200字"""

        messages = [{"role": "user", "content": system_content}]

        # ⑥ LLM 生成回复
        raw_reply = chat(messages)
        think, reply = extract_think_reply(raw_reply)

        # ⑦ 保存对话
        self.repo.save_message(session_id, "user", message, personality, emotion, tone)
        self.repo.save_message(session_id, "assistant", reply, personality, emotion, tone)

        return {
            "think": think,
            "reply": reply,
            "personality": personality,
            "emotion": emotion,
            "tone": tone,
            "examples": examples,
        }