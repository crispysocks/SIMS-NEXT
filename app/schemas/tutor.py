"""Pydantic schemas for the AI Tutor API."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


# ── Request schemas ──────────────────────────────────────────────────────────

class AnswerSubmission(BaseModel):
    """Request body for POST /answer."""
    student_answer: str


# ── Response schemas ─────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    """Response for GET /question."""
    id: str
    subject: str
    topic: str
    difficulty: str
    question_text: str
    knowledge_tags: list[str]
    learning_objectives: list[str]


class TutorResponseOut(BaseModel):
    """Pedagogical feedback from the LLM tutor."""
    explanation: str
    hint: str
    encouragement: str


class DiagnosisResultOut(BaseModel):
    """Error diagnosis result."""
    error_types: list[str]
    diagnosis_labels: list[str]
    confidence: float


class RemediationPlanOut(BaseModel):
    """Remediation plan with recommended topics."""
    recommended_topics: list[str]
    retrieval_tags: list[str]


class TutoringExplanationOut(BaseModel):
    """Plain-language explanation for a wrong answer."""
    what_is_wrong: str
    why_it_is_wrong: str
    how_to_fix: str
    similar_examples: list[str]
    retrieved_context: str
    generation_source: Optional[str] = None
    metadata: dict[str, Any] = {}


class KnowledgeSnippetOut(BaseModel):
    """A retrieved knowledge document with metadata."""
    id: str
    title: str
    topic: str
    tags: list[str]
    diagnosis_labels: list[str]
    score: float
    metadata: dict[str, Any] = {}


class AnswerResult(BaseModel):
    """Response for POST /answer."""
    is_correct: bool
    correct_answer: str
    student_answer: str
    topic: str
    tutor_response: Optional[TutorResponseOut] = None
    diagnosis: Optional[DiagnosisResultOut] = None
    remediation: Optional[RemediationPlanOut] = None
    explanation: Optional[TutoringExplanationOut] = None
    retrieved_snippets: list[KnowledgeSnippetOut] = []


class HintResponse(BaseModel):
    """Response for POST /hint."""
    hint: str
    level: int
    remaining: int


class MasteryStateOut(BaseModel):
    """Per-topic mastery state."""
    topic_id: str
    alpha: float
    beta: float
    total_attempts: int
    correct_attempts: int
    last_seen: Optional[datetime] = None
    mastery: float
    variance: float


class ProgressOut(BaseModel):
    """Full session progress snapshot."""
    mastery_states: list[MasteryStateOut]
    total_questions: int
    correct_count: int
    accuracy: float
    correct_streak: int
    wrong_streak: int
