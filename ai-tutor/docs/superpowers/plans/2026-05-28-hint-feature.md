# Hint Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add on-demand progressive hints (3 levels) that students can request while solving problems.

**Architecture:** New `get_hint()` method on TutorAgent with level-gated prompt, new `request_hint()` on TutorSession tracking per-question hint counts, new `POST /api/hint` endpoint, and a hint button in Streamlit UI. Deterministic core (engine/mastery/recommender) unchanged.

**Tech Stack:** Python, SymPy, FastAPI, Streamlit, OpenAI-compatible LLM API

---

### Task 1: Add hint prompt and get_hint() to TutorAgent

**Files:**
- Modify: `app/tutor_agent.py`

- [ ] **Step 1: Add HINT_PROMPT_TEMPLATE and HINT_FALLBACKS constants**

Add after the existing `PROMPT_TEMPLATE`:

```python
HINT_PROMPT_TEMPLATE = """\
You are a math tutor giving a hint to a student who is stuck on a problem. Respond in Chinese.

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
    2: "试着写出你已知的中间步骤，看看卡在哪里。",
    3: "回顾已学过的类似题目，对比一下解法。",
}
```

- [ ] **Step 2: Add get_hint() method to TutorAgent class**

Add after `get_feedback()`:

```python
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
```

- [ ] **Step 3: Add _call_llm_hint() internal method**

Add after `_call_llm()`:

```python
    def _call_llm_hint(
        self,
        topic: str,
        difficulty: str,
        question_text: str,
        hint_level: int,
    ) -> Optional[str]:
        prompt = HINT_PROMPT_TEMPLATE.format(
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
```

- [ ] **Step 4: Run existing tests to verify no regression**

Run: `python -m pytest tests/test_tutor_agent.py -v`
Expected: All 18 tests pass

- [ ] **Step 5: Commit**

```bash
git add app/tutor_agent.py
git commit -m "feat: add get_hint() with 3-level progressive hint prompt"
```

---

### Task 2: Add hint tracking and request_hint() to TutorSession

**Files:**
- Modify: `app/session.py`

- [ ] **Step 1: Add hint_counts to SessionState**

In the `SessionState` dataclass, add a field:

```python
    hint_counts: dict[str, int] = field(default_factory=dict)
```

- [ ] **Step 2: Add HintResponse dataclass**

Add after `AnswerFeedback`:

```python
@dataclass
class HintResponse:
    """Result of requesting a hint."""
    hint: str
    level: int
    remaining: int
```

- [ ] **Step 3: Add request_hint() to TutorSession**

Add after `submit_answer()`:

```python
    def request_hint(self) -> HintResponse:
        """Provide a progressive hint for the current question.

        Raises ValueError if no active question.
        """
        q = self._state.current_question
        if q is None:
            raise ValueError("No active question. Call next_question() first.")

        level = self._state.hint_counts.get(q.id, 0) + 1

        if level > 3:
            return HintResponse(
                hint="已达到最大提示次数，请尝试作答。",
                level=3,
                remaining=0,
            )

        hint_text = None
        if self._tutor_agent is not None:
            try:
                hint_text = self._tutor_agent.get_hint(
                    q.topic, q.difficulty, q.question_text, level,
                )
            except Exception:
                hint_text = None

        if hint_text is None:
            from app.tutor_agent import HINT_FALLBACKS
            hint_text = HINT_FALLBACKS.get(level, "请尝试作答。")

        self._state.hint_counts[q.id] = level
        remaining = 3 - level
        return HintResponse(hint=hint_text, level=level, remaining=remaining)
```

- [ ] **Step 4: Add import for HintResponse in existing imports**

No changes needed — HintResponse is defined in the same file.

- [ ] **Step 5: Clear hint_counts in reset()**

In `reset()`, change `self._state = SessionState()` — this already clears hint_counts since it's a new `SessionState` with default factory. No additional change needed.

- [ ] **Step 6: Run existing tests to verify no regression**

Run: `python -m pytest tests/test_session.py tests/test_tutor_agent.py -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add app/session.py
git commit -m "feat: add request_hint() with per-question hint count tracking"
```

---

### Task 3: Add HintResponse schema and POST /api/hint endpoint

**Files:**
- Modify: `app/schemas.py`
- Modify: `app/main.py`

- [ ] **Step 1: Add HintResponse schema**

Add after `TutorResponseOut`:

```python
class HintResponse(BaseModel):
    hint: str
    level: int
    remaining: int
```

- [ ] **Step 2: Add import in main.py**

Add `HintResponse` to the import from `app.schemas`:

```python
from app.schemas import (
    AnswerSubmission,
    AnswerResult,
    HintResponse,
    MasteryStateOut,
    ProgressOut,
    QuestionOut,
    TutorResponseOut,
)
```

- [ ] **Step 3: Add POST /api/hint endpoint**

Add after `submit_answer()`:

```python
@app.post("/api/hint", response_model=HintResponse)
def request_hint(session: TutorSession = Depends(get_session)) -> HintResponse:
    """Request a progressive hint for the current question. Up to 3 levels."""
    try:
        return session.request_hint()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 4: Run API tests to verify no regression**

Run: `python -m pytest tests/test_api.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add app/schemas.py app/main.py
git commit -m "feat: add POST /api/hint endpoint"
```

---

### Task 4: Add hint button to Streamlit UI

**Files:**
- Modify: `ui/streamlit_app.py`

- [ ] **Step 1: Add hint button in _render_question()**

Change `_render_question()` to add a hint button between the LaTeX display and the answer form. Replace the existing function body (after the LaTeX rendering) with:

Add this block after the LaTeX rendering section (after the `st.code` fallback):

```python
    # Hint button
    hint_exhausted = False
    if "tutor" in st.session_state:
        ts = st.session_state.tutor
        qid = ts._state.current_question.id if ts._state.current_question else ""
        hint_used = ts._state.hint_counts.get(qid, 0)
        hint_exhausted = hint_used >= 3

    if st.button(
        "💡 获取提示" if not hint_exhausted else "💡 提示已用完",
        disabled=hint_exhausted,
        key=f"hint_btn_{q.id}",
    ):
        hint_resp = tutor.request_hint()
        st.toast(f"提示 {hint_resp.level}/3: {hint_resp.hint}")
        st.rerun()
```

- [ ] **Step 2: Show last hint if one was requested for this question**

After the hint button, display the last hint for the current question:

```python
    if hint_used > 0:
        # Re-request the same hint info for display (hint_counts already tracks it)
        st.info(f"**💡 提示 {hint_used}/3** (剩余 {3 - hint_used} 次)")
```

Actually, we need to persist the last hint text. Let's adjust. In `SessionState`, we also store the last hint text:

Actually, simpler approach: store the hint text in session state too. But that means modifying the session module. Let me reconsider.

Simpler: Use Streamlit's session_state to store the displayed hint. Add a key like `f"hint_display_{question_id}"` in st.session_state. When hint is requested, store result there.

Let me revise the approach. The hint text comes back from `request_hint()` which we call on button click. We store it in Streamlit session_state for display:

```python
    # Show previous hints for current question
    hint_key = f"hints_{q.id}"
    if hint_key in st.session_state:
        for h in st.session_state[hint_key]:
            st.info(f"**💡 提示 {h['level']}/3** (剩余 {h['remaining']} 次): {h['hint']}")
```

And on button click, append to the list.

Let me write the final version in the plan.
```

- [ ] **Step 2 revised: Add hint button and display in _render_question()**

Replace the existing `_render_question()` function. The change is: after the LaTeX display block and before `with st.form(...)`, add:

```python
    # --- Hint feature ---
    hint_list_key = f"hints_{q.id}"
    if hint_list_key not in st.session_state:
        st.session_state[hint_list_key] = []

    hints_for_q = st.session_state[hint_list_key]
    for h in hints_for_q:
        st.info(f"**💡 提示 {h['level']}/3** (剩余 {h['remaining']} 次)\n\n{h['hint']}")

    hint_count = len(hints_for_q)
    hint_exhausted = hint_count >= 3

    if st.button(
        "💡 获取提示" if not hint_exhausted else "💡 提示已用完 (3/3)",
        disabled=hint_exhausted,
        key=f"hint_btn_{q.id}",
    ):
        hint_resp = tutor.request_hint()
        hints_for_q.append({
            "level": hint_resp.level,
            "remaining": hint_resp.remaining,
            "hint": hint_resp.hint,
        })
        st.session_state[hint_list_key] = hints_for_q
        st.rerun()
    # --- End hint feature ---
```

Note: `q` is only defined when `state.current_question` is not None, so this block must be inside the `if q is None: ... return` guard.

The existing function has:
```python
    q = state.current_question
    if q is None:
        st.info("👆 点击「下一题」开始练习")
        return
```

So `q` is guaranteed to be non-None after this check. Insert the hint block after `st.code(q.question_text, language=None)` and before `with st.form(...)`.

- [ ] **Step 3: Run UI smoke tests**

Run: `python -m pytest tests/test_ui_smoke.py -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add ui/streamlit_app.py
git commit -m "feat: add progressive hint button to Streamlit UI"
```

---

### Task 5: Run full test suite

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All 253+ tests pass
