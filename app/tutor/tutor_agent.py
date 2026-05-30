"""
Minimal LLM tutoring layer �?pedagogical interaction only.

The LLM is NOT allowed to determine correctness, update mastery,
or control recommendations. The deterministic core remains authoritative.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import os
import urllib.request

# Load .env from project root (two levels up from app/)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=True)
    except ImportError:
        pass


@dataclass
class TutorResponse:
    """Pedagogical feedback from the LLM tutor."""
    explanation: str
    hint: str
    encouragement: str


PROMPT_TEMPLATE = """\
You are a {subject_name} tutor providing feedback to a student. Respond in Chinese.

Topic: {topic}
Difficulty: {difficulty}
Question: {question_text}
Student's answer: {student_answer}
Correct answer: {correct_answer}
The student was: {result}

Return a JSON object with these fields (each under 80 characters):
- "explanation": One sentence explaining why the answer was right or wrong
- "hint": A short tip for improvement or a challenge for next time
- "encouragement": A brief encouraging message

Only return the JSON, no other text.
Example: {{"explanation": "你的答案正确，因式分解步骤是对的", "hint": "可以试试更快的十字相乘法", "encouragement": "继续加油"}}"""

HINT_PROMPT_TEMPLATE = """\
You are a {subject_name} tutor giving a hint to a student who is stuck on a problem. Respond in Chinese.

Topic: {topic}
Difficulty: {difficulty}
Question: {question_text}
Hint level: {hint_level} (1=general direction, 2=specific technique, 3=near-solution guidance)

Rules:
- Level 1: Give a general strategy or concept reminder. Do NOT mention any specific steps for this problem.
- Level 2: Point to a specific technique or intermediate step, but do NOT reveal the final answer.
- Level 3: Give detailed step-by-step guidance up to the last step, but leave the final answer for the student.

Crucially: never output the final answer. Keep your response under 100 characters.
Return a JSON object with a single field "hint".
Example: {{"hint": "回忆一下平方差公式 a²-b² = (a+b)(a-b)"}}"""

HINT_FALLBACKS = {
    1: "仔细读题，想想这道题涉及哪个知识点？",
    2: "试着写出你已知的中间步骤，看看卡在哪里�?,
    3: "回顾已学过的类似题目，对比一下解法�?,
}


class TutorAgent:
    """Calls an OpenAI-compatible LLM for pedagogical feedback.

    Failure-safe: returns None when no API key is configured or the
    LLM call fails. The core loop continues unaffected.

    Usage:
        agent = TutorAgent()                     # reads env vars
        agent = TutorAgent(mock=True)            # canned responses for testing
        resp = agent.get_feedback(...)           # TutorResponse or None
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        mock: bool = False,
        subject_name: str = "math",
    ) -> None:
        self._mock = mock
        self._subject_name = subject_name
        self._api_key = (api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")).strip()
        self._base_url = (base_url if base_url is not None else os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).strip().rstrip("/")
        self._model = (model if model is not None else os.environ.get("LLM_MODEL", "gpt-4o-mini")).strip()

    def get_feedback(
        self,
        topic: str,
        difficulty: str,
        question_text: str,
        student_answer: str,
        correct_answer: str,
        is_correct: bool,
    ) -> Optional[TutorResponse]:
        """Return pedagogical feedback, or None if unavailable."""
        if self._mock:
            return self._mock_feedback(is_correct)

        if not self._api_key:
            return None

        try:
            return self._call_llm(
                topic, difficulty, question_text,
                student_answer, correct_answer, is_correct,
            )
        except Exception:
            return None

    def get_hint(
        self,
        topic: str,
        difficulty: str,
        question_text: str,
        hint_level: int,
    ) -> Optional[str]:
        """Return a level-appropriate hint, or None if unavailable."""
        if self._mock:
            return HINT_FALLBACKS.get(hint_level, HINT_FALLBACKS[1])

        if not self._api_key:
            return HINT_FALLBACKS.get(hint_level)

        try:
            return self._call_llm_hint(topic, difficulty, question_text, hint_level)
        except Exception:
            return HINT_FALLBACKS.get(hint_level)

    # ── internal ─────────────────────────────────────────────────────────

    def _call_llm(
        self,
        topic: str,
        difficulty: str,
        question_text: str,
        student_answer: str,
        correct_answer: str,
        is_correct: bool,
    ) -> Optional[TutorResponse]:
        result = "correct" if is_correct else "incorrect"
        prompt = PROMPT_TEMPLATE.format(
            subject_name=self._subject_name,
            topic=topic,
            difficulty=difficulty,
            question_text=question_text,
            student_answer=student_answer,
            correct_answer=correct_answer,
            result=result,
        )

        body = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 256,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)

    def _call_llm_hint(
        self,
        topic: str,
        difficulty: str,
        question_text: str,
        hint_level: int,
    ) -> Optional[str]:
        prompt = HINT_PROMPT_TEMPLATE.format(
            subject_name=self._subject_name,
            topic=topic,
            difficulty=difficulty,
            question_text=question_text,
            hint_level=hint_level,
        )

        body = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 256,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return parsed.get("hint", None)

    def _parse_response(self, raw: str) -> Optional[TutorResponse]:
        try:
            parsed = json.loads(raw)
            return TutorResponse(
                explanation=parsed.get("explanation", ""),
                hint=parsed.get("hint", ""),
                encouragement=parsed.get("encouragement", ""),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def _mock_feedback(self, is_correct: bool) -> TutorResponse:
        if is_correct:
            return TutorResponse(
                explanation="回答正确！你的解题思路很清晰�?,
                hint="继续挑战更高难度吧，试试下一题�?,
                encouragement="很棒，保持这个势头！",
            )
        return TutorResponse(
            explanation="答案不对，请仔细检查计算步骤�?,
            hint="试着换一种方法，或者从已知条件重新推导�?,
            encouragement="别灰心，犯错是学习的一部分，再试一次！",
        )
