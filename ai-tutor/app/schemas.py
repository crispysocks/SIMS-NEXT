from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# -- Request -----------------------------------------------------------------

class AnswerSubmission(BaseModel):
    student_answer: str = Field(
        description="Free-text math expression, e.g. '3', '-1,-4', '2*x+3'"
    )


# -- Response ----------------------------------------------------------------

class DiagnosisResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    error_types: list[str]
    diagnosis_labels: list[str]
    confidence: float


class RemediationPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recommended_topics: list[str]
    retrieval_tags: list[str]


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject: str
    topic: str
    difficulty: str
    question_text: str
    knowledge_tags: list[str]
    learning_objectives: list[str]
    # answer is intentionally excluded -- never send correct answer to client


class AnswerResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_correct: bool
    correct_answer: str
    student_answer: str
    topic: str
    tutor_response: Optional["TutorResponseOut"] = None
    diagnosis: Optional[DiagnosisResultOut] = None
    remediation: Optional[RemediationPlanOut] = None
    explanation: Optional["TutoringExplanationOut"] = None
    retrieved_snippets: list["KnowledgeSnippetOut"] = []


class TutoringExplanationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    what_is_wrong: str
    why_it_is_wrong: str
    how_to_fix: str
    similar_examples: list[str]
    retrieved_context: str
    generation_source: Optional[str] = None
    metadata: dict[str, Any] = {}


class KnowledgeSnippetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    topic: str
    tags: list[str]
    diagnosis_labels: list[str]
    score: Optional[float] = None
    metadata: dict[str, Any] = {}


class TutorResponseOut(BaseModel):
    explanation: str
    hint: str
    encouragement: str


class HintResponse(BaseModel):
    hint: str
    level: int
    remaining: int


class MasteryStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic_id: str
    alpha: float
    beta: float
    total_attempts: int
    correct_attempts: int
    last_seen: Optional[datetime] = None
    mastery: float
    variance: float


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mastery_states: list[MasteryStateOut]
    total_questions: int
    correct_count: int
    accuracy: float
    correct_streak: int
    wrong_streak: int
