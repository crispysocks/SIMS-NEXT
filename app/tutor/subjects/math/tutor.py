"""
Math tutoring pipeline — LLM-powered explanation for wrong answers.

Implements TutoringPipeline for the math subject. Unlike the English
template-based approach, math errors are too varied for templates,
so we call an LLM to generate structured explanations.

Failure-safe: returns None on any error so the core loop is unaffected.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
import urllib.error

from app.tutor.core.subject_engine import DiagnosisResult, Question
from app.tutor.core.tutoring import (
    TutoringExplanation,
    TutoringFeedback,
    TutoringPipeline,
)

logger = logging.getLogger(__name__)

SOURCE_MATH_LLM = "math_llm"

MAX_WHAT_IS_WRONG = 500
MAX_WHY_IT_IS_WRONG = 800
MAX_HOW_TO_FIX = 500
MAX_EXAMPLES = 5

SYSTEM_PROMPT = """\
你是一位专业的数学辅导教师。你的任务是分析学生的错误答案，生成结构化的错题讲解。

要求：
1. 用中文回答，数学术语可使用英文
2. 讲解应面向中学生，语言清晰易懂
3. similar_examples 给出 2-3 道同类型练习题（只给题目，不给答案）
4. 严格按照以下JSON格式输出，不要有其他文字：
{
  "what_is_wrong": "指出学生答案具体哪里错了（1-2句话）",
  "why_it_is_wrong": "解释为什么是错的，指出正确的解题思路（2-3句话）",
  "how_to_fix": "给出改正的具体步骤（1-2句话）",
  "similar_examples": ["练习题1", "练习题2"]
}"""

_REQUIRED_KEYS = {"what_is_wrong", "why_it_is_wrong", "how_to_fix", "similar_examples"}


class MathTutoringPipeline(TutoringPipeline):
    """Math-specific tutoring pipeline powered by LLM.

    Generates structured error explanations (what/why/how + examples)
    by calling an OpenAI-compatible API.

    Usage:
        pipeline = MathTutoringPipeline()
        feedback = pipeline.explain(diagnosis, question, student_answer)
        if feedback.explanation is None:
            # LLM unavailable — no structured explanation
            ...
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = (api_key if api_key is not None else os.environ.get("LLM_API_KEY", "")).strip()
        self._base_url = (
            base_url if base_url is not None else os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        ).strip().rstrip("/")
        self._model = (model if model is not None else os.environ.get("LLM_MODEL", "gpt-4o-mini")).strip()
        self._max_retries = 2

    # -- TutoringPipeline interface -------------------------------------------

    def explain(
        self,
        diagnosis: DiagnosisResult,
        question: Question,
        student_answer: str,
    ) -> TutoringFeedback:
        """Generate tutoring feedback for a wrong math answer.

        Returns TutoringFeedback with explanation (may be None if LLM
        is unavailable) and empty knowledge_snippets.
        """
        explanation = self._generate_explanation(question, student_answer)

        return TutoringFeedback(
            diagnosis=diagnosis,
            explanation=explanation,
            knowledge_snippets=[],
        )

    # -- Internal -------------------------------------------------------------

    def _generate_explanation(
        self,
        question: Question,
        student_answer: str,
    ) -> TutoringExplanation | None:
        """Call LLM to generate a structured explanation. Returns None on failure."""
        if not self._api_key:
            return None

        user_prompt = (
            f"## 题目信息\n"
            f"- 知识点: {question.topic}\n"
            f"- 难度: {question.difficulty}\n"
            f"- 题目: {question.question_text}\n"
            f"- 学生答案: {student_answer}\n"
            f"- 正确答案: {question.answer}\n"
            f"\n"
            f"请根据以上信息生成错题讲解JSON。"
        )

        for attempt in range(self._max_retries + 1):
            try:
                raw = self._call_api(SYSTEM_PROMPT, user_prompt)
                parsed = self._parse_response(raw)
                if parsed is not None:
                    parsed.metadata = {"source": SOURCE_MATH_LLM}
                    return parsed
            except Exception:
                if attempt < self._max_retries:
                    logger.debug("Math LLM attempt %d failed, retrying", attempt + 1)
                else:
                    logger.warning("Math LLM explanation failed after %d attempts",
                                   self._max_retries + 1)

        return None

    def _call_api(self, system: str, user: str) -> str:
        """Make a single LLM API call. Raises on any HTTP/connection error."""
        url = f"{self._base_url}/chat/completions"
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
            "max_tokens": 512,
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
        """Extract and validate JSON from LLM response.

        Tries: direct parse -> fenced code block -> first brace pair.
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
