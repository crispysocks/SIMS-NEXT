"""
Smoke tests for the UI interaction pattern.

These test the exact call sequence the Streamlit UI makes,
without requiring Streamlit itself to be installed or running.
"""

import pytest
from app.engine import QuestionEngine
from app.mastery import MasteryStore
from app.recommender import Recommender
from app.session import TutorSession


TOPIC_NAMES = {
    "linear_equation": "一元一次方程",
    "quadratic_equation": "一元二次方程",
    "factoring": "因式分解",
    "derivative": "求导",
    "integral": "积分",
}


def _make_session() -> TutorSession:
    engine = QuestionEngine(seed=42)
    store = MasteryStore()
    rec = Recommender(store)
    return TutorSession(engine, store, rec)


class TestUIFlow:
    """Simulate the exact interaction pattern the Streamlit UI uses."""

    def test_initial_state(self):
        """On first load, no question and no feedback."""
        session = _make_session()
        state = session._state
        assert state.current_question is None
        assert state.last_feedback is None
        assert state.current_recommendation is None

    def test_next_question_sets_state(self):
        """Clicking '下一题' should populate current_question."""
        session = _make_session()
        q = session.next_question()
        state = session._state
        assert state.current_question is not None
        assert state.current_recommendation is not None
        assert state.last_feedback is None
        assert q.id == state.current_question.id

    def test_submit_answer_flow(self):
        """Submit answer → feedback set, question cleared."""
        session = _make_session()
        session.next_question()
        fb = session.submit_answer("3")
        state = session._state
        assert state.current_question is None
        assert state.last_feedback is not None
        assert state.last_feedback.is_correct == fb.is_correct
        assert state.last_feedback.student_answer == "3"

    def test_full_ui_loop(self):
        """Simulate: next → submit → next → submit → next."""
        session = _make_session()

        # First question
        q1 = session.next_question()
        assert session._state.current_question is not None
        fb1 = session.submit_answer(q1.answer)
        assert session._state.last_feedback is not None
        assert session._state.current_question is None

        # Second question
        q2 = session.next_question()
        assert session._state.last_feedback is None  # cleared by next_question
        assert session._state.current_question is not None
        fb2 = session.submit_answer("wrong")
        assert fb2.is_correct is False

        # Third question
        q3 = session.next_question()
        assert session._state.current_question is not None

    def test_empty_answer_handled(self):
        """Empty input should not crash."""
        session = _make_session()
        session.next_question()
        fb = session.submit_answer("")
        assert fb.is_correct is False
        assert fb.student_answer == ""

    def test_reset_clears_everything(self):
        """Reset button should clear all state."""
        session = _make_session()
        session.next_question()
        session.submit_answer("3")
        session.next_question()
        session.submit_answer("wrong")

        session.reset()
        state = session._state
        assert state.current_question is None
        assert state.last_feedback is None
        assert state.history == []
        assert state.correct_streak == 0
        assert state.wrong_streak == 0

    def test_progress_sidebar_data(self):
        """Verify data needed for progress sidebar is correct."""
        session = _make_session()
        for _ in range(5):
            q = session.next_question()
            session.submit_answer(q.answer)

        progress = session.get_progress()
        # Sidebar needs: mastery_states, accuracy, streaks, total
        assert len(progress.mastery_states) > 0
        for s in progress.mastery_states:
            assert s.topic_id in TOPIC_NAMES  # has a display name
            assert 0.0 <= s.mastery <= 1.0
            assert 0.0 <= s.variance <= 1.0
        assert 0.0 <= progress.accuracy <= 1.0

    def test_recommendation_reason_parseable(self):
        """The reason string from recommender should be parseable."""
        session = _make_session()
        session.next_question()
        rec = session._state.current_recommendation
        assert rec is not None
        assert len(rec.reason) > 0
        # Reason should contain key fields separated by semicolons
        parts = rec.reason.split(";")
        assert any("tier=" in p for p in parts)

    def test_many_ui_cycles(self):
        """50 rapid next→submit cycles should not crash."""
        session = _make_session()
        for i in range(50):
            q = session.next_question()
            # Alternate correct/wrong
            session.submit_answer(q.answer if i % 2 == 0 else "wrong")
        assert session.get_progress().total_questions == 50


class TestUIEdgeCases:
    def test_submit_without_next_raises(self):
        """UI should never call submit before next, but if it does → error."""
        session = _make_session()
        with pytest.raises(ValueError, match="No active question"):
            session.submit_answer("3")

    def test_double_next_replaces_question(self):
        """Calling next_question twice should replace the current question."""
        session = _make_session()
        q1 = session.next_question()
        q2 = session.next_question()
        assert q1.id != q2.id
        assert session._state.current_question.id == q2.id

    def test_topic_names_all_covered(self):
        """Every topic from the prereq graph should have a display name."""
        from app.recommender import DEFAULT_PREREQUISITES
        for topic in DEFAULT_PREREQUISITES:
            assert topic in TOPIC_NAMES, f"Missing display name for {topic}"


class TestDeterministicUI:
    """Same seed + same answer sequence → identical UI state."""

    def test_deterministic_session(self):
        s1 = _make_session()
        s2 = _make_session()

        for _ in range(15):
            q1 = s1.next_question()
            q2 = s2.next_question()
            assert q1.question_text == q2.question_text
            s1.submit_answer(q1.answer)
            s2.submit_answer(q2.answer)

        p1 = s1.get_progress()
        p2 = s2.get_progress()
        assert p1.total_questions == p2.total_questions
        assert p1.accuracy == p2.accuracy
        assert p1.correct_streak == p2.correct_streak
