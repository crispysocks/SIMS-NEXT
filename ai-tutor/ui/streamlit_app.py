"""
AI Math Tutor -- Streamlit Demo UI.

Launch:
    uv run streamlit run ui/streamlit_app.py --server.port 8501 --server.headless true
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so 'app' imports work regardless of CWD
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
from app.core.mastery import MasteryStore
from app.core.recommender import Recommender
from app.core.session import TutorSession
from app.tutor_agent import TutorAgent

SEED = 42

SUBJECT_CONFIG = {
    "math": {
        "icon": "📐",
        "title": "AI 数学 Tutor",
        "caption": "自适应数学学习系统 — 做题 → 掌握度更新 → 智能推荐下一题",
        "placeholder": "输入答案，如: 3 或 -1,-4 或 2*x+3 或 x**2/2",
        "footer": "Engine: SymPy",
    },
    "english": {
        "icon": "📝",
        "title": "AI 英语语法 Tutor",
        "caption": "自适应英语语法学习系统 — 做题 → 错题诊断 → 知识点讲解 → 智能推荐下一题",
        "placeholder": "输入答案，如: goes 或 have seen 或 an apple",
        "footer": "Diagnosis: rule-based | RAG: TF-IDF",
    },
}


def _init_session(subject: str) -> TutorSession:
    store = MasteryStore()
    agent = TutorAgent(subject_name=subject)

    if subject == "english":
        from app.subjects.english.engine import EnglishQuestionEngine
        from app.subjects.english.retrieval import KnowledgeRetriever
        from app.subjects.english.tutor import EnglishTutoringPipeline
        from app.subjects.english.knowledge import (
            PREREQUISITES, TOPIC_NAMES, DIFFICULTY_LABELS,
        )

        st.session_state.topic_names = TOPIC_NAMES
        st.session_state.difficulty_labels = DIFFICULTY_LABELS

        engine = EnglishQuestionEngine(seed=SEED)
        rec = Recommender(store, prerequisites=PREREQUISITES)
        retriever = KnowledgeRetriever("app/subjects/english/knowledge_base")
        pipeline = EnglishTutoringPipeline(retriever)
        return TutorSession(engine, store, rec, tutor_agent=agent, tutoring_pipeline=pipeline)

    from app.subjects.math.engine import MathQuestionEngine
    from app.subjects.math.knowledge import (
        PREREQUISITES, TOPIC_NAMES, DIFFICULTY_LABELS,
    )

    st.session_state.topic_names = TOPIC_NAMES
    st.session_state.difficulty_labels = DIFFICULTY_LABELS

    engine = MathQuestionEngine(seed=SEED)
    rec = Recommender(store, prerequisites=PREREQUISITES)
    return TutorSession(engine, store, rec, tutor_agent=agent)


# -- Session state init --------------------------------------------------------

if "subject" not in st.session_state:
    st.session_state.subject = "math"

if "tutor" not in st.session_state:
    st.session_state.tutor = _init_session(st.session_state.subject)


def _switch_subject() -> None:
    """Re-initialize session when subject changes."""
    new_subject = st.session_state.subject
    st.session_state.tutor = _init_session(new_subject)


tutor: TutorSession = st.session_state.tutor
state = tutor._state
cfg = SUBJECT_CONFIG[st.session_state.subject]

st.set_page_config(page_title=cfg["title"], page_icon=cfg["icon"], layout="wide")
st.title(f"{cfg['icon']} {cfg['title']}")
st.caption(cfg["caption"])


# -- Render helpers -----------------------------------------------------------


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
        st.caption(f"提示：{cfg['placeholder']}")

    tr = fb.tutor_response
    if tr is not None:
        with st.expander("💡 AI 导师点评", expanded=True):
            st.markdown(f"**📖 解析**: {tr.explanation}")
            st.markdown(f"**💡 提示**: {tr.hint}")
            st.markdown(f"**🌟 鼓励**: {tr.encouragement}")

    # Tutoring explanation — from tutoring pipeline (English)
    if fb.explanation is not None:
        source = fb.explanation.metadata.get("source", "")
        source_labels = {
            "rag_llm": "📖 错题讲解 (RAG 生成)",
            "template_fallback": "📖 错题讲解 (模板降级)",
            "deterministic_fallback": "📖 错题讲解 (确定性降级)",
        }
        expander_label = source_labels.get(source, "📖 错题讲解")

        with st.expander(expander_label, expanded=True):
            st.markdown(f"**❌ 问题所在**: {fb.explanation.what_is_wrong}")
            st.markdown(f"**📚 为什么错**: {fb.explanation.why_it_is_wrong}")
            st.markdown(f"**🔧 怎么改正**: {fb.explanation.how_to_fix}")
            if fb.explanation.similar_examples:
                st.markdown("**✅ 正确示例**:")
                for ex in fb.explanation.similar_examples:
                    st.markdown(f"- {ex}")
            if fb.explanation.retrieved_context:
                with st.expander("📖 详细知识点"):
                    st.markdown(fb.explanation.retrieved_context)

    # Retrieved knowledge snippets — transparency view
    if fb.knowledge_snippets:
        with st.expander("🔍 检索结果 (相似度排序)", expanded=False):
            for i, ks in enumerate(fb.knowledge_snippets, 1):
                st.markdown(f"**{i}. {ks.title}** (相关性: {ks.score:.3f})")
                st.caption(f"🏷️ 主题: {ks.topic}")
                if ks.tags:
                    st.caption(f"🏷️ 标签: {', '.join(ks.tags)}")
                if ks.diagnosis_labels:
                    st.caption(f"🏥 诊断: {', '.join(ks.diagnosis_labels)}")
                source_file = ks.metadata.get("_source_file", "")
                if source_file:
                    st.caption(f"📁 来源: {source_file}")

    # Diagnosis/remediation — only display if non-empty (math returns empty for now)
    if fb.diagnosis and fb.diagnosis.diagnosis_labels:
        with st.expander("🔍 诊断分析", expanded=False):
            st.markdown(f"**错误类型**: {', '.join(fb.diagnosis.error_types)}")
            st.markdown(f"**诊断标签**: {', '.join(fb.diagnosis.diagnosis_labels)}")
            st.caption(f"置信度: {fb.diagnosis.confidence:.0%}")

    if fb.remediation and fb.remediation.recommended_topics:
        with st.expander("📋 补救建议", expanded=False):
            st.markdown(f"**推荐主题**: {', '.join(fb.remediation.recommended_topics)}")
            st.markdown(f"**检索标签**: {', '.join(fb.remediation.retrieval_tags)}")


def _render_question() -> None:
    """Display the current question with answer input form."""
    q = state.current_question
    if q is None:
        st.info("👆 点击「下一题」开始练习")
        return

    topic_names = st.session_state.get("topic_names", {})
    diff_labels = st.session_state.get("difficulty_labels", {})

    topic_name = topic_names.get(q.topic, q.topic)
    diff_label = diff_labels.get(q.difficulty, q.difficulty)

    st.subheader(f"{topic_name}")
    st.caption(f"难度: {diff_label}")

    # Math: render LaTeX; English: render plain text
    if st.session_state.subject == "math":
        tex = q.question_text.replace("$", "")
        try:
            st.latex(tex)
        except Exception:
            st.code(q.question_text, language=None)
    else:
        st.markdown(f"### {q.question_text}")

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
            placeholder=cfg["placeholder"],
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
            st.session_state.tutor = _init_session(st.session_state.subject)
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
    topic_names = st.session_state.get("topic_names", {})

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
                names = [topic_names.get(b, b) for b in blocked_list]
                st.caption(f"🚫 前置未解锁: {', '.join(names)}")
            except Exception:
                st.caption(f"🚫 前置未解锁: {blocked_raw}")

        elif part.startswith("anti-frustration:"):
            detail = part.split(":", 1)[1].strip()
            st.warning(f"🛡️ 挫折保护: {detail}")

        elif "switched topic" in part:
            detail = part.strip()
            st.info(f"🔀 {detail}")


# -- Layout --------------------------------------------------------------------

main, side = st.columns([3, 2])

with side:
    # Subject selector
    st.subheader("📚 学科选择")
    st.radio(
        "选择学科",
        options=["math", "english"],
        format_func=lambda x: "📐 数学" if x == "math" else "📝 英语语法",
        key="subject",
        on_change=_switch_subject,
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("📊 学习进度")

    progress = tutor.get_progress()
    topic_names = st.session_state.get("topic_names", {})

    for s in progress.mastery_states:
        name = topic_names.get(s.topic_id, s.topic_id)
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
    f"{cfg['title']} MVP | "
    f"{cfg['footer']} | "
    "Mastery: Beta-Binomial | "
    "Recommender: 3-tier deterministic | "
    f"Seed: {SEED}"
)
