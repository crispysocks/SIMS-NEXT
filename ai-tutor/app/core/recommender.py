from dataclasses import dataclass
from typing import Optional

from app.core.mastery import MasteryStore


FRUSTRATION_WINDOW = 3
PREREQ_THRESHOLD = 0.6
CHALLENGE_LOW = 0.4
CHALLENGE_HIGH = 0.7


@dataclass
class Recommendation:
    """Explainable recommendation for the next question."""

    topic: str
    difficulty: str
    reason: str


class Recommender:
    """Deterministic topic + difficulty selector.

    Inputs:
      - mastery state (from MasteryStore)
      - per-topic variance
      - recent answer history (in-memory)
      - prerequisite graph (supplied by caller, not hardcoded)

    Policy (evaluated in order):
      1. Prerequisite gating — block topics whose prereqs are below 0.6.
      2. Challenge zone [0.4, 0.7] — prefer topics where the student is learning.
      3. Uncertainty exploration — within the same tier, prefer higher variance.
      4. Anti-frustration — after 3 consecutive wrong answers, lower difficulty
         and avoid the most recent topic.

    Difficulty mapping (from the chosen topic's mastery):
      mastery < 0.4  → easy
      0.4 – 0.7     → medium
      > 0.7         → hard
    """

    def __init__(
        self,
        mastery_store: MasteryStore,
        prerequisites: dict[str, list[str]],
    ) -> None:
        self._store = mastery_store
        self._prereqs = prerequisites
        self._history: list[tuple[str, bool]] = []  # (topic_id, correct)

    # ── public API ───────────────────────────────────────────────────────

    def recommend(self) -> Recommendation:
        """Return the next topic and difficulty with an explanation."""
        topics = list(self._prereqs.keys())
        states = {t: self._store.get(t) for t in topics}

        eligible, blocked = self._apply_gating(states)
        chosen_topic, tier_label = self._select_topic(eligible, states)
        difficulty = self._map_difficulty(states[chosen_topic].mastery)
        chosen_topic, difficulty, reason_extra = self._apply_anti_frustration(
            chosen_topic, difficulty, eligible, states
        )

        reason = self._build_reason(tier_label, blocked, reason_extra)
        return Recommendation(topic=chosen_topic, difficulty=difficulty, reason=reason)

    def record(self, topic: str, correct: bool) -> None:
        """Record an answer outcome for frustration detection."""
        self._history.append((topic, correct))

    # ── policy steps ─────────────────────────────────────────────────────

    def _apply_gating(
        self, states: dict[str, "MasteryState"]
    ) -> tuple[list[str], list[str]]:
        eligible: list[str] = []
        blocked: list[str] = []
        for topic, prereqs in self._prereqs.items():
            if all(states[p].mastery >= PREREQ_THRESHOLD for p in prereqs):
                eligible.append(topic)
            else:
                blocked.append(topic)
        return eligible, blocked

    def _select_topic(
        self,
        eligible: list[str],
        states: dict[str, "MasteryState"],
    ) -> tuple[str, str]:
        """Pick the best topic from eligible candidates.

        Returns (topic, tier_label).
        """
        # Tier 1 — challenge zone [0.4, 0.7]: pick highest variance
        in_zone = [
            t for t in eligible if CHALLENGE_LOW <= states[t].mastery <= CHALLENGE_HIGH
        ]
        if in_zone:
            return max(in_zone, key=lambda t: states[t].variance), "challenge"

        # Tier 2 — below 0.4: pick highest mastery (closest to entering zone)
        below = [t for t in eligible if states[t].mastery < CHALLENGE_LOW]
        if below:
            return max(below, key=lambda t: states[t].mastery), "reinforcement"

        # Tier 3 — all > 0.7: spiral review, pick lowest mastery
        chosen = min(eligible, key=lambda t: states[t].mastery)
        return chosen, "spiral"

    def _map_difficulty(self, mastery: float) -> str:
        if mastery < CHALLENGE_LOW:
            return "easy"
        if mastery <= CHALLENGE_HIGH:
            return "medium"
        return "hard"

    def _apply_anti_frustration(
        self,
        chosen_topic: str,
        difficulty: str,
        eligible: list[str],
        states: dict[str, "MasteryState"],
    ) -> tuple[str, str, str]:
        """Detect frustration and adjust topic/difficulty.

        Returns (chosen_topic, difficulty, reason_extra).
        """
        extra = ""
        if not self._is_frustrated():
            return chosen_topic, difficulty, extra

        # Lower difficulty one step
        lowered = {"hard": "medium", "medium": "easy"}.get(difficulty, "easy")
        extra = f"anti-frustration: {difficulty}->{lowered}"

        # Avoid repeating the frustrating topic
        last_topic = self._history[-1][0]
        if last_topic == chosen_topic and len(eligible) > 1:
            remaining = [t for t in eligible if t != last_topic]
            alt, _ = self._select_topic(remaining, states)
            extra += f", switched topic {chosen_topic}->{alt}"
            return alt, lowered, extra

        return chosen_topic, lowered, extra

    def _is_frustrated(self) -> bool:
        if len(self._history) < FRUSTRATION_WINDOW:
            return False
        return all(not correct for _, correct in self._history[-FRUSTRATION_WINDOW:])

    def _build_reason(
        self, tier: str, blocked: list[str], extra: str
    ) -> str:
        parts = [f"tier={tier}"]
        if blocked:
            parts.append(f"blocked={blocked}")
        if extra:
            parts.append(extra)
        return "; ".join(parts)
