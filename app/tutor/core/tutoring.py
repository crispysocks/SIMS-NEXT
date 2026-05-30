"""
Tutoring feedback pipeline �?shared dataclasses and interface.

The tutoring pipeline is an optional injectable that enriches
AnswerFeedback with plain-language explanations and retrieved
knowledge context when a student answers incorrectly.

This module defines the interface (TutoringPipeline ABC) and the
data structures. Subject-specific implementations live in their
respective subject modules (e.g. subjects/english/tutor.py).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.tutor.core.subject_engine import DiagnosisResult, Question


@dataclass
class KnowledgeSnippet:
    """A retrieved knowledge document with metadata."""

    id: str
    title: str
    topic: str
    tags: list[str] = field(default_factory=list)
    diagnosis_labels: list[str] = field(default_factory=list)
    content: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TutoringExplanation:
    """Plain-language explanation for a wrong answer.

    All fields are deterministic �?no LLM output.
    """

    what_is_wrong: str
    why_it_is_wrong: str
    how_to_fix: str
    similar_examples: list[str] = field(default_factory=list)
    retrieved_context: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TutoringFeedback:
    """Complete tutoring feedback bundle for a wrong answer."""

    diagnosis: DiagnosisResult
    explanation: TutoringExplanation | None
    knowledge_snippets: list[KnowledgeSnippet] = field(default_factory=list)


class TutoringPipeline(ABC):
    """Interface for subject-specific tutoring explanation pipelines.

    Each subject module provides an implementation that wires:
        diagnosis -> retrieval -> explanation

    The session never imports subject-specific code �?it only
    depends on this ABC.
    """

    @abstractmethod
    def explain(
        self,
        diagnosis: DiagnosisResult,
        question: Question,
        student_answer: str,
    ) -> TutoringFeedback:
        """Generate a full tutoring feedback for a wrong answer.

        Returns TutoringFeedback with explanation and knowledge context.
        When the retriever finds no matching documents, explanation
        fields are populated from fallback templates.
        """
        ...
