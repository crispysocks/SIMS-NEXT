import pytest
from app.mastery import MasteryStore, MasteryState
from app.recommender import (
    Recommender,
    Recommendation,
    DEFAULT_PREREQUISITES,
    FRUSTRATION_WINDOW,
    CHALLENGE_LOW,
    CHALLENGE_HIGH,
)


def _set_mastery(store: MasteryStore, topic: str, alpha: float, beta: float) -> None:
    """Helper: directly set alpha/beta for a topic to simulate mastery level."""
    state = store.get(topic)
    state.alpha = alpha
    state.beta = beta
    total = int(alpha + beta - 6)
    state.total_attempts = max(0, total)
    state.correct_attempts = max(0, int(alpha - 3))


def _set_all_above_zone(store: MasteryStore) -> None:
    """Set every topic well above 0.7 (= spiral zone) so they don't interfere."""
    for t in DEFAULT_PREREQUISITES:
        _set_mastery(store, t, alpha=30, beta=3)  # mastery ≈ 0.91


# ── Recommendation dataclass ─────────────────────────────────────────────────

class TestRecommendation:
    def test_fields(self):
        r = Recommendation(topic="linear_equation", difficulty="easy", reason="test")
        assert r.topic == "linear_equation"
        assert r.difficulty == "easy"
        assert r.reason == "test"


# ── Prerequisite gating ──────────────────────────────────────────────────────

class TestPrerequisiteGating:
    def test_blocks_quadratic_when_linear_below_threshold(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=4, beta=6)  # mastery = 0.4
        recommender = Recommender(store)
        r = recommender.recommend()
        # quadratic_equation should be blocked (prereq linear_equation < 0.6)
        assert r.topic != "quadratic_equation"
        assert "blocked" in r.reason
        assert "quadratic_equation" in r.reason

    def test_blocks_integral_when_derivative_below_threshold(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=30, beta=3)  # mastery high
        _set_mastery(store, "derivative", alpha=3, beta=3)  # mastery = 0.5
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.topic != "integral"
        assert "integral" in r.reason

    def test_unblocks_when_prereq_meets_threshold(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=30, beta=10)  # mastery = 0.75
        _set_mastery(store, "quadratic_equation", alpha=3, beta=3)  # mastery = 0.5
        recommender = Recommender(store)
        r = recommender.recommend()
        # quadratic_equation is eligible and in challenge zone
        assert r.topic == "quadratic_equation"
        assert "blocked" not in r.reason or "quadratic_equation" not in r.reason

    def test_no_prereqs_topic_always_eligible(self):
        store = MasteryStore()
        # linear_equation has no prereqs
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.topic == "linear_equation"  # only eligible topic initially


# ── Challenge zone priority ──────────────────────────────────────────────────

class TestChallengeZone:
    def test_prefers_in_zone_over_below_zone(self):
        store = MasteryStore()
        _set_all_above_zone(store)
        _set_mastery(store, "quadratic_equation", alpha=5, beta=5)  # mastery = 0.5 → in zone
        _set_mastery(store, "factoring", alpha=4, beta=6)  # mastery = 0.4 → in zone
        recommender = Recommender(store)
        r = recommender.recommend()
        # quadratic (0.5) and factoring (0.4) are in zone, others above zone
        assert r.topic in ("quadratic_equation", "factoring")
        assert "challenge" in r.reason

    def test_prefers_in_zone_over_above_zone(self):
        store = MasteryStore()
        _set_all_above_zone(store)
        _set_mastery(store, "quadratic_equation", alpha=5, beta=5)  # = 0.5 → in zone
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.topic == "quadratic_equation"

    def test_picks_higher_variance_within_zone(self):
        store = MasteryStore()
        _set_all_above_zone(store)
        # Two topics in zone, factoring has fewer samples → higher variance
        _set_mastery(store, "quadratic_equation", alpha=5, beta=5)  # variance = 25/(100*11) ≈ 0.0227
        _set_mastery(store, "factoring", alpha=4, beta=3)  # variance = 12/(49*8) ≈ 0.0306
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.topic == "factoring"

    def test_no_zone_falls_back_to_reinforcement(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=3, beta=7)  # mastery = 0.3 → below zone
        recommender = Recommender(store)
        r = recommender.recommend()
        # linear_equation is the only eligible (no prereqs), below zone
        assert r.topic == "linear_equation"
        assert "reinforcement" in r.reason


# ── Reinforcement tier ───────────────────────────────────────────────────────

class TestReinforcement:
    def test_picks_highest_mastery_below_zone(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=30, beta=3)  # ≈ 0.91 (prereq for others)
        _set_mastery(store, "quadratic_equation", alpha=4, beta=7)  # ≈ 0.36
        _set_mastery(store, "factoring", alpha=3, beta=7)  # ≈ 0.30
        _set_mastery(store, "derivative", alpha=3, beta=7)  # ≈ 0.30
        recommender = Recommender(store)
        r = recommender.recommend()
        # quadratic (0.36) is highest below zone
        assert r.topic == "quadratic_equation"
        assert "reinforcement" in r.reason


# ── Spiral review ────────────────────────────────────────────────────────────

class TestSpiralReview:
    def test_picks_lowest_mastery_when_all_above_zone(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=30, beta=3)  # ≈ 0.91
        _set_mastery(store, "quadratic_equation", alpha=20, beta=3)  # ≈ 0.87
        _set_mastery(store, "factoring", alpha=50, beta=3)  # ≈ 0.94
        _set_mastery(store, "derivative", alpha=30, beta=3)  # ≈ 0.91
        _set_mastery(store, "integral", alpha=10, beta=3)  # ≈ 0.77 → lowest
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.topic == "integral"
        assert "spiral" in r.reason


# ── Difficulty mapping ───────────────────────────────────────────────────────

class TestDifficultyMapping:
    def test_low_mastery_gives_easy(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=3, beta=7)  # mastery = 0.3
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.difficulty == "easy"

    def test_mid_mastery_gives_medium(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=5, beta=5)  # mastery = 0.5
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.difficulty == "medium"

    def test_high_mastery_gives_hard(self):
        store = MasteryStore()
        _set_all_above_zone(store)  # all ≈ 0.91 → spiral zone
        recommender = Recommender(store)
        r = recommender.recommend()
        # All above 0.7, spiral picks lowest — but all have same mastery.
        # Difficulty mapping depends on chosen topic's mastery, which is > 0.7.
        assert r.difficulty == "hard"

    def test_boundary_at_0_4(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=4, beta=6)  # mastery = 0.4
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.difficulty == "medium"  # 0.4 is the boundary, enters medium

    def test_boundary_at_0_7(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=7, beta=3)  # mastery = 0.7
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.difficulty == "medium"  # 0.7 is still medium


# ── Anti-frustration ─────────────────────────────────────────────────────────

class TestAntiFrustration:
    def test_lowers_difficulty_after_3_wrong(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=5, beta=5)  # mastery = 0.5 → medium
        recommender = Recommender(store)
        # Record 3 wrong answers
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        r = recommender.recommend()
        assert r.difficulty == "easy"
        assert "anti-frustration" in r.reason

    def test_avoids_same_topic_after_3_wrong(self):
        store = MasteryStore()
        _set_all_above_zone(store)
        # Two challenge-zone topics — factoring has higher variance (normally preferred)
        _set_mastery(store, "quadratic_equation", alpha=5, beta=5)  # mastery = 0.5
        _set_mastery(store, "factoring", alpha=4, beta=3)  # higher variance → normally preferred
        recommender = Recommender(store)
        # Get frustrated on factoring (the higher-variance pick)
        recommender.record("factoring", False)
        recommender.record("factoring", False)
        recommender.record("factoring", False)
        r = recommender.recommend()
        # Should switch away from factoring
        assert r.topic != "factoring"
        assert "switched topic" in r.reason

    def test_no_switch_when_only_one_eligible(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=3, beta=7)  # mastery = 0.3
        recommender = Recommender(store)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        r = recommender.recommend()
        # Only linear_equation is eligible (no prereqs), can't switch
        assert r.topic == "linear_equation"
        assert r.difficulty == "easy"  # still lowers difficulty

    def test_does_not_trigger_before_3_wrong(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=5, beta=5)  # mastery = 0.5 → medium
        recommender = Recommender(store)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        # Only 2 wrong — not frustrated yet
        r = recommender.recommend()
        assert r.difficulty == "medium"

    def test_resets_after_correct(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=5, beta=5)
        recommender = Recommender(store)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", True)  # correct resets
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        r = recommender.recommend()
        assert r.difficulty == "medium"  # not frustrated yet (only 2 wrong since last correct)

    def test_hard_lowered_to_medium(self):
        store = MasteryStore()
        _set_all_above_zone(store)  # all ≈ 0.91 → difficulty would be hard
        recommender = Recommender(store)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        recommender.record("linear_equation", False)
        r = recommender.recommend()
        assert r.difficulty == "medium"


# ── Determinism ──────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_state_same_recommendation(self):
        s1 = MasteryStore()
        _set_mastery(s1, "linear_equation", alpha=30, beta=3)
        _set_mastery(s1, "quadratic_equation", alpha=5, beta=5)
        _set_mastery(s1, "factoring", alpha=4, beta=3)
        r1 = Recommender(s1)
        r1.record("linear_equation", True)

        s2 = MasteryStore()
        _set_mastery(s2, "linear_equation", alpha=30, beta=3)
        _set_mastery(s2, "quadratic_equation", alpha=5, beta=5)
        _set_mastery(s2, "factoring", alpha=4, beta=3)
        r2 = Recommender(s2)
        r2.record("linear_equation", True)

        rec1 = r1.recommend()
        rec2 = r2.recommend()
        assert rec1.topic == rec2.topic
        assert rec1.difficulty == rec2.difficulty


# ── Reason output ────────────────────────────────────────────────────────────

class TestReason:
    def test_reason_not_empty(self):
        store = MasteryStore()
        recommender = Recommender(store)
        r = recommender.recommend()
        assert len(r.reason) > 0

    def test_reason_includes_tier(self):
        store = MasteryStore()
        _set_mastery(store, "linear_equation", alpha=5, beta=5)  # challenge zone
        recommender = Recommender(store)
        r = recommender.recommend()
        assert "challenge" in r.reason

    def test_reason_includes_blocked_when_gated(self):
        store = MasteryStore()
        # linear is low, so everything with prereqs is blocked
        _set_mastery(store, "linear_equation", alpha=3, beta=7)
        recommender = Recommender(store)
        r = recommender.recommend()
        assert "blocked" in r.reason


# ── record() method ──────────────────────────────────────────────────────────

class TestRecord:
    def test_history_grows(self):
        store = MasteryStore()
        recommender = Recommender(store)
        assert len(recommender._history) == 0
        recommender.record("linear_equation", True)
        assert len(recommender._history) == 1
        recommender.record("linear_equation", False)
        assert len(recommender._history) == 2

    def test_history_stores_correctly(self):
        store = MasteryStore()
        recommender = Recommender(store)
        recommender.record("t1", True)
        recommender.record("t2", False)
        assert recommender._history[0] == ("t1", True)
        assert recommender._history[1] == ("t2", False)


# ── Custom prerequisite graph ────────────────────────────────────────────────

class TestCustomPrereqGraph:
    def test_custom_graph_used(self):
        store = MasteryStore()
        custom = {
            "a": [],
            "b": ["a"],
        }
        recommender = Recommender(store, prerequisites=custom)
        # 'a' has no prereqs → eligible; 'b' needs 'a' ≥ 0.6
        r = recommender.recommend()
        assert r.topic == "a"
        assert "b" in r.reason

    def test_default_graph_covers_all_topics(self):
        store = MasteryStore()
        recommender = Recommender(store)
        r = recommender.recommend()
        assert r.topic in DEFAULT_PREREQUISITES
