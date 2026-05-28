import math
import pytest
from app.mastery import MasteryStore, MasteryState, PRIOR_ALPHA, PRIOR_BETA


class TestMasteryState:
    def test_initial_prior(self):
        state = MasteryState(topic_id="linear_eq")
        assert state.alpha == PRIOR_ALPHA
        assert state.beta == PRIOR_BETA
        assert state.total_attempts == 0
        assert state.correct_attempts == 0
        assert state.last_seen is None

    def test_mastery_is_posterior_mean(self):
        state = MasteryState(topic_id="t", alpha=5, beta=5)
        assert state.mastery == 0.5

    def test_mastery_after_correct(self):
        state = MasteryState(topic_id="t", alpha=4, beta=3)
        assert state.mastery == 4 / 7

    def test_mastery_after_wrong(self):
        state = MasteryState(topic_id="t", alpha=3, beta=5)
        assert state.mastery == 3 / 8

    def test_variance_decreases_with_more_samples(self):
        uncertain = MasteryState(topic_id="t", alpha=3, beta=3)
        certain = MasteryState(topic_id="t", alpha=30, beta=30)
        assert uncertain.variance > certain.variance

    def test_variance_is_zero_for_extreme_certainty(self):
        """Variance → 0 as alpha+beta → ∞ with fixed ratio."""
        state = MasteryState(topic_id="t", alpha=300, beta=300)
        assert state.variance < 0.001

    def test_mastery_is_readonly(self):
        state = MasteryState(topic_id="t")
        with pytest.raises(AttributeError):
            state.mastery = 0.9


class TestMasteryStore:
    def test_get_creates_topic_with_prior(self):
        store = MasteryStore()
        state = store.get("linear_eq")
        assert state.alpha == PRIOR_ALPHA
        assert state.beta == PRIOR_BETA
        assert state.mastery == 0.5
        assert state.total_attempts == 0

    def test_get_same_topic_returns_same_object(self):
        store = MasteryStore()
        s1 = store.get("t1")
        s2 = store.get("t1")
        assert s1 is s2

    def test_update_correct_increments_alpha(self):
        store = MasteryStore()
        state = store.update("linear_eq", correct=True)
        assert state.alpha == PRIOR_ALPHA + 1
        assert state.beta == PRIOR_BETA
        assert state.mastery > 0.5

    def test_update_wrong_increments_beta(self):
        store = MasteryStore()
        state = store.update("linear_eq", correct=False)
        assert state.alpha == PRIOR_ALPHA
        assert state.beta == PRIOR_BETA + 1
        assert state.mastery < 0.5

    def test_update_tracks_attempts(self):
        store = MasteryStore()
        store.update("t1", correct=True)
        store.update("t1", correct=False)
        store.update("t1", correct=True)
        state = store.get("t1")
        assert state.total_attempts == 3
        assert state.correct_attempts == 2

    def test_update_sets_last_seen(self):
        store = MasteryStore()
        from datetime import datetime, timezone

        before = datetime.now(timezone.utc)
        state = store.update("t1", correct=True)
        after = datetime.now(timezone.utc)
        assert state.last_seen is not None
        assert before <= state.last_seen <= after

    def test_mastery_converges_upward_with_repeated_success(self):
        store = MasteryStore()
        for _ in range(10):
            store.update("t1", correct=True)
        state = store.get("t1")
        assert state.mastery > 0.8

    def test_mastery_converges_downward_with_repeated_failure(self):
        store = MasteryStore()
        for _ in range(10):
            store.update("t1", correct=False)
        state = store.get("t1")
        assert state.mastery < 0.3

    def test_get_all_returns_all_topics(self):
        store = MasteryStore()
        store.update("t1", correct=True)
        store.update("t2", correct=False)
        store.update("t3", correct=True)
        all_states = store.get_all()
        assert len(all_states) == 3
        topic_ids = {s.topic_id for s in all_states}
        assert topic_ids == {"t1", "t2", "t3"}

    def test_reset_clears_all_state(self):
        store = MasteryStore()
        store.update("t1", correct=True)
        store.update("t2", correct=False)
        store.reset()
        assert store.get_all() == []
        # After reset, getting a topic creates a fresh prior
        state = store.get("t1")
        assert state.alpha == PRIOR_ALPHA
        assert state.total_attempts == 0

    def test_variance_decreases_with_evidence(self):
        store = MasteryStore()
        initial_var = store.get("t1").variance
        for _ in range(5):
            store.update("t1", correct=True)
        after5_var = store.get("t1").variance
        assert after5_var < initial_var
        for _ in range(20):
            store.update("t1", correct=True)
        after25_var = store.get("t1").variance
        assert after25_var < after5_var

    def test_uncertainty_higher_at_midpoint(self):
        """Variance is highest when mastery ≈ 0.5, lower at extremes."""
        store = MasteryStore()
        # After 3 correct + 3 wrong → still near 0.5
        for _ in range(3):
            store.update("balanced", correct=True)
            store.update("balanced", correct=False)
        balanced = store.get("balanced")

        # After many correct → near 1.0
        for _ in range(20):
            store.update("skilled", correct=True)
        skilled = store.get("skilled")

        assert balanced.variance > skilled.variance
