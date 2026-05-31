from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.tutor.core.subject_engine import (
    SubjectEngine,
    Question,
    ValidationResult,
    DiagnosisResult,
    RemediationPlan,
)
from app.tutor.core.mastery import MasteryStore, MasteryState
from app.tutor.core.recommender import Recommender, Recommendation
from app.tutor.core.tutoring import (
    TutoringPipeline,
    TutoringExplanation,
    KnowledgeSnippet,
)
from app.tutor.tutor_agent import TutorAgent, TutorResponse


@dataclass
class AnswerRecord:
    """A single answered question in session history."""

    question_id: str
    topic: str
    difficulty: str
    question_text: str
    student_answer: str
    correct_answer: str
    is_correct: bool
    timestamp: datetime
    error_types: list[str] = field(default_factory=list)
    diagnosis_labels: list[str] = field(default_factory=list)
    remediation_topics: list[str] = field(default_factory=list)
    explanation: Optional[TutoringExplanation] = None


@dataclass
class AnswerFeedback:
    """Result of submitting an answer."""

    is_correct: bool
    correct_answer: str
    student_answer: str
    topic: str
    tutor_response: Optional[TutorResponse] = None
    diagnosis: Optional[DiagnosisResult] = None
    remediation: Optional[RemediationPlan] = None
    explanation: Optional[TutoringExplanation] = None
    knowledge_snippets: list[KnowledgeSnippet] = field(default_factory=list)


@dataclass
class HintResponse:
    """Result of requesting a hint."""

    hint: str
    level: int
    remaining: int


@dataclass
class Progress:
    """Snapshot of current session progress."""

    mastery_states: list[MasteryState]
    total_questions: int
    correct_count: int
    accuracy: float
    correct_streak: int
    wrong_streak: int
    history: list[AnswerRecord]


@dataclass
class SessionState:
    """Mutable state held by TutorSession."""

    current_question: Optional[Question] = None
    current_recommendation: Optional[Recommendation] = None
    correct_streak: int = 0
    wrong_streak: int = 0
    history: list[AnswerRecord] = field(default_factory=list)
    last_feedback: Optional[AnswerFeedback] = None
    hint_counts: dict[str, int] = field(default_factory=dict)


class TutorSession:
    """Deterministic tutoring loop connecting engine -> mastery -> recommender.

    Usage:
        engine = MathQuestionEngine(seed=42)
        store = MasteryStore()
        rec = Recommender(store, prerequisites=PREREQUISITES)
        session = TutorSession(engine, store, rec)

        q = session.next_question()        # get a question
        fb = session.submit_answer("3")    # submit answer
        # fb.is_correct, fb.correct_answer ...

        q2 = session.next_question()       # next question (adapted)
    """

    def __init__(
        self,
        engine: SubjectEngine,
        mastery_store: MasteryStore,
        recommender: Recommender,
        tutor_agent: Optional[TutorAgent] = None,
        tutoring_pipeline: Optional[TutoringPipeline] = None,
    ) -> None:
        self._engine = engine
        self._mastery = mastery_store
        self._recommender = recommender
        self._tutor_agent = tutor_agent
        self._tutoring_pipeline = tutoring_pipeline
        self._state = SessionState()

    # -- public API -----------------------------------------------------------

    def next_question(self) -> Question:
        """Get the next recommended question. Must call before submit_answer()."""
        rec = self._recommender.recommend()
        question = self._engine.generate(rec.topic, rec.difficulty)
        self._state.current_question = question
        self._state.current_recommendation = rec
        self._state.last_feedback = None
        return question

    def submit_answer(self, student_answer: str) -> AnswerFeedback:
        """Validate, diagnose, and update all state.

        Raises ValueError if no active question (call next_question() first).

        Three-phase pipeline (diagnosis and remediation are structural
        placeholders -- math returns empty results for now):
          1. Validation  -- correctness check
          2. Diagnosis   -- error classification (reserved)
          3. Remediation -- remediation selection (reserved)
        """
        q = self._state.current_question
        if q is None:
            raise ValueError("No active question. Call next_question() first.")

        # Phase 1 -- Validation
        validation = self._engine.validate(student_answer, q.answer)

        # Phase 2 -- Diagnosis (reserved; math returns empty for now)
        diagnosis = self._engine.diagnose(student_answer, q.answer, q)

        # Phase 3 -- Remediation (reserved; math returns empty for now)
        remediation = self._engine.plan_remediation(diagnosis)

        # Phase 4 -- Knowledge Retrieval + Explanation (when pipeline configured)
        explanation = None
        knowledge_snippets: list[KnowledgeSnippet] = []
        if not validation.is_correct and self._tutoring_pipeline is not None:
            tf = self._tutoring_pipeline.explain(
                diagnosis=diagnosis,
                question=q,
                student_answer=student_answer,
            )
            explanation = tf.explanation
            knowledge_snippets = tf.knowledge_snippets

        # Mastery update (unchanged order)
        self._mastery.update(q.topic, validation.is_correct)
        self._recommender.record(q.topic, validation.is_correct)
        self._update_streaks(validation.is_correct)
        self._record_history(q, student_answer, validation, diagnosis, remediation, explanation)

        tr = self._get_tutor_feedback(q, student_answer, validation.is_correct)

        feedback = AnswerFeedback(
            is_correct=validation.is_correct,
            correct_answer=q.answer,
            student_answer=student_answer,
            topic=q.topic,
            tutor_response=tr,
            diagnosis=diagnosis,
            remediation=remediation,
            explanation=explanation,
            knowledge_snippets=knowledge_snippets,
        )
        self._state.last_feedback = feedback
        self._state.current_question = None
        self._state.current_recommendation = None
        return feedback

    def request_hint(self) -> HintResponse:
        """Provide a progressive hint for the current question.

        Raises ValueError if no active question.
        """
        q = self._state.current_question
        if q is None:
            raise ValueError("No active question. Call next_question() first.")

        level = self._state.hint_counts.get(q.id, 0) + 1

        if level > 3:
            return HintResponse(
                hint="已达到最大提示次数，请尝试作答。",
                level=3,
                remaining=0,
            )

        hint_text = None
        if self._tutor_agent is not None:
            try:
                hint_text = self._tutor_agent.get_hint(
                    q.topic, q.difficulty, q.question_text, level,
                )
            except Exception:
                hint_text = None

        if hint_text is None:
            from app.tutor.tutor_agent import HINT_FALLBACKS
            hint_text = HINT_FALLBACKS.get(level, "请尝试作答。")

        self._state.hint_counts[q.id] = level
        remaining = 3 - level
        return HintResponse(hint=hint_text, level=level, remaining=remaining)

    def get_progress(self) -> Progress:
        """Return a snapshot of current session progress."""
        total = len(self._state.history)
        correct_count = sum(1 for r in self._state.history if r.is_correct)
        return Progress(
            mastery_states=self._mastery.get_all(),
            total_questions=total,
            correct_count=correct_count,
            accuracy=correct_count / total if total > 0 else 0.0,
            correct_streak=self._state.correct_streak,
            wrong_streak=self._state.wrong_streak,
            history=list(self._state.history),
        )

    def reset(self) -> None:
        """Reset all state -- mastery, recommender history, and session."""
        self._mastery.reset()
        self._state = SessionState()

    # -- internal -------------------------------------------------------------

    def _get_tutor_feedback(
        self, q: Question, student_answer: str, correct: bool
    ) -> Optional[TutorResponse]:
        if self._tutor_agent is None:
            return None
        try:
            return self._tutor_agent.get_feedback(
                topic=q.topic,
                difficulty=q.difficulty,
                question_text=q.question_text,
                student_answer=student_answer,
                correct_answer=q.answer,
                is_correct=correct,
            )
        except Exception:
            return None

    def _update_streaks(self, correct: bool) -> None:
        if correct:
            self._state.correct_streak += 1
            self._state.wrong_streak = 0
        else:
            self._state.wrong_streak += 1
            self._state.correct_streak = 0

    def _record_history(
        self,
        q: Question,
        student_answer: str,
        validation: ValidationResult,
        diagnosis: DiagnosisResult,
        remediation: RemediationPlan,
        explanation: Optional[TutoringExplanation] = None,
    ) -> None:
        record = AnswerRecord(
            question_id=q.id,
            topic=q.topic,
            difficulty=q.difficulty,
            question_text=q.question_text,
            student_answer=student_answer,
            correct_answer=q.answer,
            is_correct=validation.is_correct,
            timestamp=datetime.now(timezone.utc),
            error_types=diagnosis.error_types,
            diagnosis_labels=diagnosis.diagnosis_labels,
            remediation_topics=remediation.recommended_topics,
            explanation=explanation,
        )
        self._state.history.append(record)
