"""
AI Math Tutor — Streamlit Demo UI.

Launch:
    uv run streamlit run ui/streamlit_app.py --server.port 8501 --server.headless true
"""

import streamlit as st
from app.engine import QuestionEngine
from app.mastery import MasteryStore
from app.recommender import Recommender
from app.session import TutorSession
from app.tutor_agent import TutorAgent

TOPIC_NAMES = {
    "linear_equation": "一元一次方程",
    "quadratic_equation": "一元二次方程",
    "factoring": "因式分解",
    "derivative": "求导",
    "integral": "积分",
}

DIFFICULTY_LABELS = {
    "easy": "简单",
    "medium": "中等",
    "hard": "困难",
}

SEED = 42


def _init_session() -> TutorSession:
    engine = QuestionEngine(seed=SEED)
    store = MasteryStore()
    rec = Recommender(store)
    agent = TutorAgent()
    return TutorSession(engine, store, rec, tutor_agent=agent)


if "tutor" not in st.session_state:
    st.session_state.tutor = _init_session()


def _reset() -> None:
    st.session_state.tutor = _init_session()


tutor: TutorSession = st.session_state.tutor
state = tutor._state

st.set_page_config(page_title="AI 数学 Tutor", page_icon="📐", layout="wide")
st.title("📐 AI 数学 Tutor")
st.caption("自适应数学学习系统 — 做题 → 掌握度更新 → 智能推荐下一题")


# ── Render helpers (must be defined before use) ──────────────────────────────

def _render_feedback() -> None:
    """Show the result of the last submitted answer."""
    fb = state.last_feedback
    if fb is None:
        return

    if fb.is_correct:
        st.success("✓ 回答正确！")
    else:
        st.error("✗ 回答错误")
        st.markdown(f"**正确答案**: `{fb.correct_answer}`")
        st.caption("提示：输入数学表达式，如 `3`、`-1,-4`、`2*x+3`、`x**2/2`")

    tr = fb.tutor_response
    if tr is not None:
        with st.expander("💡 AI 导师点评", expanded=True):
            st.markdown(f"**📖 解析**: {tr.explanation}")
            st.markdown(f"**💡 提示**: {tr.hint}")
            st.markdown(f"**🌟 鼓励**: {tr.encouragement}")


def _render_question() -> None:
    """Display the current question with answer input form."""
    q = state.current_question
    if q is None:
        st.info("👆 点击「下一题」开始练习")
        return

    topic_name = TOPIC_NAMES.get(q.topic, q.topic)
    diff_label = DIFFICULTY_LABELS.get(q.difficulty, q.difficulty)

    st.subheader(f"{topic_name}")
    st.caption(f"难度: {diff_label}")

    tex = q.question_text.replace("$", "")
    try:
        st.latex(tex)
    except Exception:
        st.code(q.question_text, language=None)

    hint_list_key = f"hints_{q.id}"
    if hint_list_key not in st.session_state:
        st.session_state[hint_list_key] = []

    hints_for_q = st.session_state[hint_list_key]
    for h in hints_for_q:
        st.info(f"**💡 提示 {h['level']}/3** (剩余 {h['remaining']} 次)\n\n{h['hint']}")

    hint_exhausted = len(hints_for_q) >= 3

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

    with st.form("answer_form", clear_on_submit=True):
        answer = st.text_input(
            "你的答案",
            placeholder='输入答案，如: 3 或 -1,-4 或 2*x+3 或 x**2/2',
            key="answer_input",
        )
        submitted = st.form_submit_button("提交答案", type="primary", use_container_width=True)

        if submitted:
            if answer.strip():
                tutor.submit_answer(answer.strip())
            else:
                tutor.submit_answer("")
            st.rerun()


def _render_controls() -> None:
    """Next question and reset buttons."""
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        if st.button("▶ 下一题", use_container_width=True):
            tutor.next_question()
            st.rerun()

    with c2:
        if st.button("🔄 重置", use_container_width=True):
            _reset()
            st.rerun()

    with c3:
        if progress.total_questions > 0:
            st.caption(
                f"已完成 {progress.total_questions} 题 | "
                f"正确率 {progress.accuracy:.0%}"
            )


def _parse_reason(reason: str) -> None:
    """Display the recommendation reason in human-readable form."""
    parts = [p.strip() for p in reason.split(";") if p.strip()]

    for part in parts:
        if part.startswith("tier="):
            tier = part.split("=", 1)[1]
            tier_labels = {
                "challenge": "🎯 挑战区 (mastery 0.4-0.7)",
                "reinforcement": "📚 巩固区 (mastery < 0.4)",
                "spiral": "🔄 复习区 (mastery > 0.7)",
            }
            st.markdown(tier_labels.get(tier, f"层级: {tier}"))

        elif part.startswith("blocked="):
            blocked_raw = part.split("=", 1)[1]
            import ast
            try:
                blocked_list = ast.literal_eval(blocked_raw)
                names = [TOPIC_NAMES.get(b, b) for b in blocked_list]
                st.caption(f"🚫 前置未解锁: {', '.join(names)}")
            except Exception:
                st.caption(f"🚫 前置未解锁: {blocked_raw}")

        elif part.startswith("anti-frustration:"):
            detail = part.split(":", 1)[1].strip()
            st.warning(f"🛡️ 挫折保护: {detail}")

        elif "switched topic" in part:
            detail = part.strip()
            st.info(f"🔀 {detail}")


# ── Layout ───────────────────────────────────────────────────────────────────

main, side = st.columns([3, 2])

with side:
    st.subheader("📊 学习进度")

    progress = tutor.get_progress()
    for s in progress.mastery_states:
        name = TOPIC_NAMES.get(s.topic_id, s.topic_id)
        m = s.mastery
        if m < 0.4:
            color = "#ef4444"
        elif m <= 0.7:
            color = "#f59e0b"
        else:
            color = "#22c55e"

        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(f"**{name}**")
            st.progress(m)
        with col_b:
            st.markdown(
                f"<span style='color:{color};font-weight:bold;font-size:1.1em;'>{m:.2f}</span>",
                unsafe_allow_html=True,
            )
        st.caption(f"  不确定度: {s.variance:.4f} | 答题: {s.total_attempts}")

    st.divider()
    st.subheader("📈 统计")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("正确率", f"{progress.accuracy:.0%}")
    with c2:
        st.metric("连对", progress.correct_streak)
    with c3:
        st.metric("连错", progress.wrong_streak)

    total = progress.total_questions
    correct = progress.correct_count
    wrong = total - correct
    if total > 0:
        st.write(f"总题数: {total} (✓{correct} / ✗{wrong})")

    if state.current_recommendation is not None:
        st.divider()
        st.subheader("💡 推荐理由")
        rec = state.current_recommendation
        _parse_reason(rec.reason)

with main:
    _render_feedback()
    _render_question()
    _render_controls()

st.divider()
st.caption(
    "AI Math Tutor MVP | "
    "Engine: SymPy | "
    "Mastery: Beta-Binomial | "
    "Recommender: 3-tier deterministic | "
    f"Seed: {SEED}"
)
