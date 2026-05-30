"""Subject engine interface �?the contract every subject module must fulfill.

Defines four data structures and the SubjectEngine ABC that decouples
the core tutoring loop from subject-specific question generation,
validation, diagnosis, and remediation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Question:
    """A generated question with its canonical answer and learning metadata."""

    id: str
    topic: str
    difficulty: str
    question_text: str
    answer: str
    subject: str = ""
    knowledge_tags: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Correctness only �?no diagnosis, no remediation."""

    is_correct: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosisResult:
    """What went wrong �?error classification and misconception labels."""

    error_types: list[str] = field(default_factory=list)
    diagnosis_labels: list[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RemediationPlan:
    """What to teach next �?recommended topics and retrieval tags."""

    recommended_topics: list[str] = field(default_factory=list)
    retrieval_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SubjectEngine(ABC):
    """Contract for subject-specific engines.

    Each subject (math, english, ...) provides an implementation.
    The core tutoring loop only depends on this ABC �?never on
    subject-specific types or libraries.
    """

    @abstractmethod
    def generate(self, topic: str, difficulty: str) -> Question:
        """Generate a question for the given topic and difficulty."""
        ...

    @abstractmethod
    def validate(self, student_answer: str, correct_answer: str) -> ValidationResult:
        """Check correctness of a student answer against the canonical answer."""
        ...

    @abstractmethod
    def diagnose(
        self,
        student_answer: str,
        correct_answer: str,
        question: Question,
    ) -> DiagnosisResult:
        """Analyze an answer for misconceptions and error patterns."""
        ...

    @abstractmethod
    def plan_remediation(self, diagnosis: DiagnosisResult) -> RemediationPlan:
        """Select remediation topics and retrieval tags based on diagnosis."""
        ...

    @abstractmethod
    def get_knowledge_tags(self, topic: str) -> list[str]:
        """Return the fine-grained knowledge tags for a topic."""
        ...

    @property
    @abstractmethod
    def topics(self) -> tuple[str, ...]:
        """All topics this subject engine can generate questions for."""
        ...

    @property
    @abstractmethod
    def difficulties(self) -> tuple[str, ...]:
        """All difficulty levels this subject engine supports."""
        ...
