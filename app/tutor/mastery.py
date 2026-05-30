from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

PRIOR_ALPHA = 3.0
PRIOR_BETA = 3.0


@dataclass
class MasteryState:
    """Per-topic mastery belief modeled as a Beta distribution.

    Prior: Beta(3, 3) â€?symmetric, mean 0.5, high initial uncertainty.
    After each answer: correct â†?alpha += 1, wrong â†?beta += 1.
    """

    topic_id: str
    alpha: float = PRIOR_ALPHA
    beta: float = PRIOR_BETA
    total_attempts: int = 0
    correct_attempts: int = 0
    last_seen: Optional[datetime] = None

    @property
    def mastery(self) -> float:
        """Posterior mean â€?estimated probability of correct answer."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        """Posterior variance â€?higher means less confident.

        Used by the recommender for tie-breaking:
        when two topics have similar mastery, prefer the one with higher variance.
        """
        a, b = self.alpha, self.beta
        return (a * b) / ((a + b) ** 2 * (a + b + 1))


class MasteryStore:
    """In-memory mastery tracker for all topics.

    Pure Python dict-based storage. No database dependency.
    Thread-safe for single-user use (not designed for concurrency).
    """

    def __init__(self) -> None:
        self._states: dict[str, MasteryState] = {}

    def _ensure(self, topic_id: str) -> MasteryState:
        """Get or create state for a topic with Beta(3,3) prior."""
        if topic_id not in self._states:
            self._states[topic_id] = MasteryState(topic_id=topic_id)
        return self._states[topic_id]

    def update(self, topic_id: str, correct: bool) -> MasteryState:
        """Record an answer outcome and return the updated state.

        Args:
            topic_id: The topic the question belonged to.
            correct: True if the student answered correctly.

        Returns:
            The updated MasteryState after incorporating the observation.
        """
        state = self._ensure(topic_id)
        state.total_attempts += 1
        if correct:
            state.alpha += 1.0
            state.correct_attempts += 1
        else:
            state.beta += 1.0
        state.last_seen = datetime.now(timezone.utc)
        return state

    def get(self, topic_id: str) -> MasteryState:
        """Return the current state for a topic, creating it with defaults if unseen."""
        return self._ensure(topic_id)

    def get_all(self) -> list[MasteryState]:
        """Return all tracked topics."""
        return list(self._states.values())

    def reset(self) -> None:
        """Clear all mastery state."""
        self._states.clear()
