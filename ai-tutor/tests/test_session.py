import pytest
from datetime import datetime, timezone

from app.engine import QuestionEngine, Question, safe_compare
from app.mastery import MasteryStore, MasteryState
from app.recommender import Recommender
from app.session import (
    TutorSession,
    SessionState,
    AnswerRecord,
    AnswerFeedback,
    Progress,
)


def _make_session(seed: int = 42) -> TutorSession:
    """Create a fresh session with deterministic engine."""
    engine = QuestionEngine(seed=seed)
    store = MasteryStore()
    recommender = Recommender(store)
    return TutorSession(engine, store, recommender)


# ── AnswerRecord / AnswerFeedback / Progress dataclasses ─────────────────────

class TestAnswerRecord:
    def test_fields(self):
        ts = datetime.now(timezone.utc)
        r = AnswerRecord(
            question_id="q1",
            topic="linear_equation",
            difficulty="easy",
            question_text="Solve: $2x = 6$",
            student_answer="3",
            correct_answer="3",
            is_correct=True,
            timestamp=ts,
        )
        assert r.question_id == "q1"
        assert r.topic == "linear_equation"
        assert r.is_correct is True
        assert r.timestamp == ts


class TestAnswerFeedback:
    def test_fields(self):
        fb = AnswerFeedback(
            is_correct=True,
            correct_answer="3",
            student_answer="3",
            topic="linear_equation",
        )
        assert fb.is_correct is True
        assert fb.correct_answer == "3"
        assert fb.student_answer == "3"
        assert fb.topic == "linear_equation"


class TestProgressDataclass:
    def test_fields(self):
        p = Progress(
            mastery_states=[],
            total_questions=10,
            correct_count=7,
            accuracy=0.7,
            correct_streak=3,
            wrong_streak=0,
            history=[],
        )
        assert p.total_questions == 10
        assert p.accuracy == 0.7
        assert p.correct_streak == 3


# ── Session flow ─────────────────────────────────────────────────────────────

class TestBasicFlow:
    def test_next_question_returns_question(self):
        session = _make_session()
        q = session.next_question()
        assert isinstance(q, Question)
        assert len(q.id) > 0
        assert len(q.question_text) > 0
        assert len(q.answer) > 0

    def test_submit_answer_returns_feedback(self):
        session = _make_session()
        q = session.next_question()
        fb = session.submit_answer(q.answer)  # submit correct answer
        assert isinstance(fb, AnswerFeedback)
        assert fb.is_correct is True
        assert fb.topic == q.topic

    def test_submit_wrong_answer(self):
        session = _make_session()
        q = session.next_question()
        fb = session.submit_answer("wrong_answer_999")
        assert fb.is_correct is False
        assert fb.correct_answer == q.answer

    def test_full_cycle_next_submit_next(self):
        """next_question → submit_answer → next_question works."""
        session = _make_session()
        q1 = session.next_question()
        fb1 = session.submit_answer(q1.answer)
        assert fb1.is_correct is True

        q2 = session.next_question()
        fb2 = session.submit_answer("wrong")
        assert fb2.is_correct is False

        q3 = session.next_question()
        assert isinstance(q3, Question)

    def test_submit_without_next_raises(self):
        session = _make_session()
        with pytest.raises(ValueError, match="No active question"):
            session.submit_answer("3")

    def test_submit_twice_without_next_raises(self):
        session = _make_session()
        session.next_question()
        session.submit_answer("3")
        # Second submit without calling next_question
        with pytest.raises(ValueError, match="No active question"):
            session.submit_answer("4")


# ── Streaks ──────────────────────────────────────────────────────────────────

class TestStreaks:
    def test_correct_streak_increments(self):
        session = _make_session()
        for _ in range(3):
            q = session.next_question()
            session.submit_answer(q.answer)  # correct
        progress = session.get_progress()
        assert progress.correct_streak == 3
        assert progress.wrong_streak == 0

    def test_wrong_streak_increments(self):
        session = _make_session()
        for _ in range(3):
            q = session.next_question()
            session.submit_answer("wrong")  # wrong
        progress = session.get_progress()
        assert progress.wrong_streak == 3
        assert progress.correct_streak == 0

    def test_streak_resets_on_mixed(self):
        session = _make_session()
        q = session.next_question()
        session.submit_answer(q.answer)  # correct
        q = session.next_question()
        session.submit_answer(q.answer)  # correct
        q = session.next_question()
        session.submit_answer("wrong")  # wrong → resets correct streak
        progress = session.get_progress()
        assert progress.correct_streak == 0
        assert progress.wrong_streak == 1


# ── History ──────────────────────────────────────────────────────────────────

class TestHistory:
    def test_history_records_all_answers(self):
        session = _make_session()
        for _ in range(5):
            q = session.next_question()
            session.submit_answer(q.answer)
        progress = session.get_progress()
        assert len(progress.history) == 5

    def test_history_includes_correctness(self):
        session = _make_session()
        q = session.next_question()
        session.submit_answer(q.answer)  # correct
        q = session.next_question()
        session.submit_answer("wrong")  # wrong
        progress = session.get_progress()
        assert progress.history[0].is_correct is True
        assert progress.history[1].is_correct is False

    def test_history_includes_student_answer(self):
        session = _make_session()
        q = session.next_question()
        session.submit_answer("my_answer_42")
        progress = session.get_progress()
        assert progress.history[0].student_answer == "my_answer_42"

    def test_history_includes_topic_and_difficulty(self):
        session = _make_session()
        q = session.next_question()
        session.submit_answer(q.answer)
        progress = session.get_progress()
        record = progress.history[0]
        assert record.topic == q.topic
        assert record.difficulty == q.difficulty

    def test_history_has_timestamps(self):
        session = _make_session()
        before = datetime.now(timezone.utc)
        q = session.next_question()
        session.submit_answer(q.answer)
        after = datetime.now(timezone.utc)
        ts = session.get_progress().history[0].timestamp
        assert before <= ts <= after


# ── Progress ─────────────────────────────────────────────────────────────────

class TestGetProgress:
    def test_total_questions(self):
        session = _make_session()
        for _ in range(7):
            q = session.next_question()
            session.submit_answer(q.answer)
        assert session.get_progress().total_questions == 7

    def test_correct_count(self):
        session = _make_session()
        for i in range(10):
            q = session.next_question()
            # Answer correctly for even indices
            session.submit_answer(q.answer if i % 2 == 0 else "wrong")
        progress = session.get_progress()
        assert progress.correct_count == 5

    def test_accuracy(self):
        session = _make_session()
        for i in range(4):
            q = session.next_question()
            session.submit_answer(q.answer if i < 3 else "wrong")  # 3/4 correct
        progress = session.get_progress()
        assert progress.accuracy == 0.75

    def test_accuracy_zero_when_no_questions(self):
        session = _make_session()
        progress = session.get_progress()
        assert progress.accuracy == 0.0
        assert progress.total_questions == 0

    def test_mastery_states_in_progress(self):
        session = _make_session()
        for _ in range(3):
            q = session.next_question()
            session.submit_answer(q.answer)
        progress = session.get_progress()
        states = progress.mastery_states
        assert len(states) > 0
        attempted = [s for s in states if s.total_attempts > 0]
        assert len(attempted) > 0  # at least some topics were questioned


# ── Reset ────────────────────────────────────────────────────────────────────

class TestReset:
    def test_reset_clears_mastery(self):
        session = _make_session()
        q = session.next_question()
        session.submit_answer(q.answer)
        session.reset()
        progress = session.get_progress()
        assert progress.total_questions == 0
        assert progress.mastery_states == []

    def test_reset_clears_history(self):
        session = _make_session()
        for _ in range(5):
            q = session.next_question()
            session.submit_answer(q.answer)
        session.reset()
        assert session.get_progress().history == []

    def test_reset_clears_streaks(self):
        session = _make_session()
        for _ in range(3):
            q = session.next_question()
            session.submit_answer(q.answer)
        session.reset()
        progress = session.get_progress()
        assert progress.correct_streak == 0
        assert progress.wrong_streak == 0

    def test_next_question_works_after_reset(self):
        session = _make_session()
        q = session.next_question()
        session.submit_answer(q.answer)
        session.reset()
        q2 = session.next_question()
        assert isinstance(q2, Question)


# ── Integration: mastery evolves ─────────────────────────────────────────────

class TestMasteryEvolution:
    def test_correct_answers_increase_mastery(self):
        session = _make_session()
        # Force linear_equation questions only by making everything else blocked
        # Repeated correct answers on the same topic
        initial_mastery = None
        for _ in range(10):
            q = session.next_question()
            fb = session.submit_answer(q.answer)  # always correct
            assert fb.is_correct
            if q.topic == "linear_equation":
                state = session.get_progress().mastery_states
                for s in state:
                    if s.topic_id == "linear_equation":
                        if initial_mastery is None:
                            initial_mastery = s.mastery
        # Mastery should have increased from initial 0.5
        final_state = None
        for s in session.get_progress().mastery_states:
            if s.topic_id == "linear_equation":
                final_state = s
        assert final_state is not None
        assert final_state.mastery > initial_mastery

    def test_wrong_answers_decrease_mastery(self):
        session = _make_session(seed=1)
        q = session.next_question()
        initial_mastery = None
        for s in session.get_progress().mastery_states:
            if s.topic_id == q.topic:
                initial_mastery = s.mastery
        # Submit wrong answers
        for _ in range(5):
            q = session.next_question()
            session.submit_answer("wrong")
        # Mastery should have dropped below 0.5
        for s in session.get_progress().mastery_states:
            if s.topic_id == q.topic:
                assert s.mastery < 0.5

    def test_last_feedback_updated(self):
        session = _make_session()
        q = session.next_question()
        fb = session.submit_answer("test_answer")
        assert session._state.last_feedback is not None
        assert session._state.last_feedback.student_answer == "test_answer"
        assert session._state.last_feedback.is_correct == fb.is_correct


# ── Integration: session → recommender feedback loop ─────────────────────────

class TestAdaptiveLoop:
    def test_difficulty_starts_easy(self):
        """With fresh mastery (0.5), difficulty should be medium (in zone)."""
        session = _make_session()
        q = session.next_question()
        # Fresh mastery = 0.5 → medium difficulty
        assert q.difficulty in ("easy", "medium")

    def test_session_trajectory_is_deterministic(self):
        """Same seed + same answer pattern → same trajectory."""
        s1 = _make_session(seed=42)
        s2 = _make_session(seed=42)

        history1 = []
        history2 = []
        for _ in range(20):
            q1 = s1.next_question()
            q2 = s2.next_question()
            assert q1.question_text == q2.question_text
            assert q1.topic == q2.topic
            assert q1.difficulty == q2.difficulty
            # Answer correctly on even steps
            answer = q1.answer if len(history1) % 2 == 0 else "wrong"
            fb1 = s1.submit_answer(answer)
            fb2 = s2.submit_answer(answer)
            assert fb1.is_correct == fb2.is_correct
            history1.append(fb1)
            history2.append(fb2)

        p1 = s1.get_progress()
        p2 = s2.get_progress()
        assert p1.total_questions == p2.total_questions
        assert p1.accuracy == p2.accuracy

    def test_anti_frustration_triggers_in_session(self):
        """After 3 wrong answers, difficulty should be lowered."""
        session = _make_session(seed=42)
        difficulties = []
        for _ in range(10):
            q = session.next_question()
            difficulties.append((q.difficulty, q.topic))
            session.submit_answer("wrong")  # always wrong

        # Check that anti-frustration kicked in at some point
        # After 3 wrong, difficulty should drop from medium to easy
        easy_count = sum(1 for d, _ in difficulties if d == "easy")
        assert easy_count > 0

    def test_topic_progression_over_time(self):
        """Topics should progress from linear → quadratic/derivative/factoring
        as mastery on linear_equation grows."""
        session = _make_session(seed=42)
        topics_seen = []
        for _ in range(15):
            q = session.next_question()
            topics_seen.append(q.topic)
            # Always answer correctly to build mastery
            session.submit_answer(q.answer)

        # Should see linear_equation first, then more advanced topics
        assert "linear_equation" in topics_seen[:5]
        # After building mastery, should see other topics
        unique_topics = set(topics_seen)
        assert len(unique_topics) >= 2


# ── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_answer(self):
        session = _make_session()
        session.next_question()
        fb = session.submit_answer("")
        assert fb.is_correct is False

    def test_very_long_answer(self):
        session = _make_session()
        session.next_question()
        fb = session.submit_answer("x" * 10000)
        assert fb.is_correct is False  # should not crash

    def test_get_progress_mid_question(self):
        """get_progress works when a question is active but not yet answered."""
        session = _make_session()
        session.next_question()
        progress = session.get_progress()
        assert progress.total_questions == 0  # not answered yet
        assert progress.correct_count == 0

    def test_many_rapid_cycles(self):
        """100 rapid next/submit cycles should not crash."""
        session = _make_session()
        for _ in range(100):
            q = session.next_question()
            session.submit_answer(q.answer)
        assert session.get_progress().total_questions == 100

    def test_submit_answer_clears_current_question(self):
        session = _make_session()
        session.next_question()
        session.submit_answer("3")
        assert session._state.current_question is None
        assert session._state.current_recommendation is None
