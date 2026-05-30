"""LLM explanation generator — OpenAI-compatible API → TutoringExplanation.

Isolated from the tutoring pipeline. One public method:
    generate(...) -> TutoringExplanation | None

Never returns raw LLM output. All responses go through:
    JSON parse → required-key validation → length capping
On any failure, returns None so the caller falls back.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
import urllib.error

from app.tutor.core.tutoring import TutoringExplanation

logger = logging.getLogger(__name__)

# Generation source constants
SOURCE_RAG_LLM = "rag_llm"
SOURCE_TEMPLATE_FALLBACK = "template_fallback"
SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

# Max char lengths for validated fields
MAX_WHAT_IS_WRONG = 500
MAX_WHY_IT_IS_WRONG = 800
MAX_HOW_TO_FIX = 500
MAX_EXAMPLES = 5

SYSTEM_PROMPT = """\
你是一位专业的英语语法教师。你的任务是分析学生的错误答案，结合提供的语法知识点，生成结构化的错题讲解。

要求：
1. 必须基于提供的【知识点】内容来解释，不要编造规则
2. 如果知识点中没有明确提及某个规则，如实说明"该错误在当前知识点中未详细覆盖"
3. 用中文回答，语法术语使用英文
4. 讲解应面向英语学习者（母语为中文），语言要清晰易懂
5. 严格按照以下JSON格式输出，不要有其他文字：
{
  "what_is_wrong": "指出学生答案具体哪里错了（1-2句话）",
  "why_it_is_wrong": "解释为什么是错的，引用相关语法规则（2-3句话）",
  "how_to_fix": "给出改正的具体步骤或思路（1-2句话）",
  "similar_examples": ["正确例句1", "正确例句2", "正确例句3"]
}"""

_REQUIRED_KEYS = {"what_is_wrong", "why_it_is_wrong", "how_to_fix", "similar_examples"}


class LLMExplanationGenerator:
    """Generate structured tutoring explanations via an OpenAI-compatible API.

    Usage:
        gen = LLMExplanationGenerator()
        explanation = gen.generate(
            question_text="She ___ to school every day.",
            student_answer="go",
            correct_answer="goes",
            diagnosis_labels=["missing_third_person_s"],
            context="## 知识点\n...",
        )
        if explanation is None:
            # fall back to template explanation
            ...
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        ).strip().rstrip("/")
        self._model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._max_retries = 2

    # -- Public API -------------------------------------------------------------

    def generate(
        self,
        question_text: str,
        student_answer: str,
        correct_answer: str,
        diagnosis_labels: list[str],
        context: str,
    ) -> TutoringExplanation | None:
        """Generate a structured explanation via LLM.

        Returns None if:
        - No API key configured
        - API call fails after retries
        - Response parsing fails (invalid JSON, missing keys)
        - Any required field exceeds max length after capping
        """
        if not self._api_key:
            return None

        system = SYSTEM_PROMPT
        user = self._build_user_prompt(
            question_text=question_text,
            student_answer=student_answer,
            correct_answer=correct_answer,
            diagnosis_labels=diagnosis_labels,
            context=context,
        )

        for attempt in range(self._max_retries + 1):
            try:
                raw = self._call_api(system, user)
                parsed = self._parse_response(raw)
                if parsed is not None:
                    parsed.metadata = {"source": SOURCE_RAG_LLM}
                    return parsed
            except Exception:
                if attempt < self._max_retries:
                    logger.debug("LLM call attempt %d failed, retrying", attempt + 1)
                else:
                    logger.warning("LLM explanation generation failed after %d attempts",
                                   self._max_retries + 1)

        return None

    # -- Internal ---------------------------------------------------------------

    @staticmethod
    def _build_user_prompt(
        question_text: str,
        student_answer: str,
        correct_answer: str,
        diagnosis_labels: list[str],
        context: str,
    ) -> str:
        labels_str = ", ".join(diagnosis_labels) if diagnosis_labels else "(无)"
        return (
            f"## 题目信息\n"
            f"- 题目: {question_text}\n"
            f"- 学生答案: {student_answer}\n"
            f"- 正确答案: {correct_answer}\n"
            f"- 诊断标签: {labels_str}\n"
            f"\n"
            f"{context}\n"
            f"\n"
            f"请根据以上信息生成错题讲解JSON。"
        )

    def _call_api(self, system: str, user: str) -> str:
        url = f"{self._base_url}/chat/completions"
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Connection error: {e.reason}") from e

        return result["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_response(raw: str) -> TutoringExplanation | None:
        """Extract and parse JSON from LLM response.

        Tries in order:
        1. Direct JSON parse
        2. ```json ... ``` fenced block
        3. First { ... } brace pair
        """
        raw = raw.strip()

        # 1. Direct parse
        data = _try_json(raw)
        if data is not None:
            return _validate_and_build(data)

        # 2. Fenced block: ```json ... ```
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            data = _try_json(m.group(1))
            if data is not None:
                return _validate_and_build(data)

        # 3. First brace pair
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = _try_json(m.group(0))
            if data is not None:
                return _validate_and_build(data)

        return None


def _try_json(text: str) -> dict | None:
    """Parse JSON string, return None on any failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _validate_and_build(data: dict) -> TutoringExplanation | None:
    """Validate required keys and length caps. Returns None if invalid."""
    if not isinstance(data, dict):
        return None

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        return None

    examples = data.get("similar_examples", [])
    if not isinstance(examples, list):
        examples = []
    examples = [str(e) for e in examples[:MAX_EXAMPLES]]

    what = str(data.get("what_is_wrong", "")).strip()[:MAX_WHAT_IS_WRONG]
    why = str(data.get("why_it_is_wrong", "")).strip()[:MAX_WHY_IT_IS_WRONG]
    how = str(data.get("how_to_fix", "")).strip()[:MAX_HOW_TO_FIX]

    if not what or not why or not how:
        return None

    return TutoringExplanation(
        what_is_wrong=what,
        why_it_is_wrong=why,
        how_to_fix=how,
        similar_examples=examples,
    )
