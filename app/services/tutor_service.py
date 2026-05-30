"""AI Tutor service — business logic layer for the tutoring module.

Phase 1: in-memory session (no database). The TutorSession is a global
singleton managed by this service.

Supports both math and english subjects with optional RAG pipeline.
"""

import os

from app.tutor.core.mastery import MasteryStore
from app.tutor.core.recommender import Recommender
from app.tutor.core.session import TutorSession, Progress, AnswerFeedback, HintResponse
from app.tutor.tutor_agent import TutorAgent


SEED = 42

# Default subject — can be overridden via environment variable
DEFAULT_SUBJECT = os.environ.get("AI_TUTOR_SUBJECT", "math")


def _create_math_session() -> TutorSession:
    """Create a TutorSession wired for the math subject."""
    from app.tutor.subjects.math.engine import MathQuestionEngine
    from app.tutor.subjects.math.knowledge import PREREQUISITES

    _api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    agent = TutorAgent(subject_name="math", mock=not bool(_api_key))
    store = MasteryStore()
    engine = MathQuestionEngine(seed=SEED)
    rec = Recommender(store, prerequisites=PREREQUISITES)
    return TutorSession(engine, store, rec, tutor_agent=agent)


def _create_english_session() -> TutorSession:
    """Create a TutorSession wired for the english subject with optional RAG."""
    from app.tutor.subjects.english.engine import EnglishQuestionEngine
    from app.tutor.subjects.english.knowledge import PREREQUISITES as ENG_PREREQS

    _api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    agent = TutorAgent(subject_name="english", mock=not bool(_api_key))
    store = MasteryStore()
    engine = EnglishQuestionEngine(seed=SEED)
    rec = Recommender(store, prerequisites=ENG_PREREQS)

    # Try to create RAG pipeline
    tutoring_pipeline = None
    try:
        from app.tutor.rag.factory import create_pipeline
        tutoring_pipeline = create_pipeline("english")
    except Exception:
        # Fallback to deterministic pipeline
        try:
            from app.tutor.subjects.english.retrieval import KnowledgeRetriever
            from app.tutor.subjects.english.tutor import EnglishTutoringPipeline
            kb_path = os.environ.get(
                "RAG_KB_PATH",
                "app/tutor/subjects/english/knowledge_base"
            )
            retriever = KnowledgeRetriever(kb_path)
            tutoring_pipeline = EnglishTutoringPipeline(retriever)
        except Exception:
            pass

    return TutorSession(
        engine, store, rec,
        tutor_agent=agent,
        tutoring_pipeline=tutoring_pipeline,
    )


# Subject -> session factory mapping
_SESSION_FACTORIES = {
    "math": _create_math_session,
    "english": _create_english_session,
}


class TutorService:
    """Manages the tutoring session lifecycle.

    Phase 1: uses a module-level singleton session (in-memory, no DB).
    Supports switching between subjects.
    """

    def __init__(self, subject: str | None = None) -> None:
        self._subject = subject or DEFAULT_SUBJECT
        self._session: TutorSession | None = None

    @property
    def subject(self) -> str:
        """Current subject name."""
        return self._subject

    def _ensure_session(self) -> TutorSession:
        """Lazy-initialize the TutorSession singleton."""
        if self._session is None:
            factory = _SESSION_FACTORIES.get(self._subject)
            if factory is None:
                raise ValueError(
                    f"Unknown subject: {self._subject}. "
                    f"Valid: {list(_SESSION_FACTORIES.keys())}"
                )
            self._session = factory()
        return self._session

    def switch_subject(self, subject: str) -> None:
        """Switch to a different subject, resetting the session.

        Args:
            subject: "math" or "english"

        Raises:
            ValueError: if subject is not supported
        """
        if subject not in _SESSION_FACTORIES:
            raise ValueError(
                f"Unknown subject: {subject}. "
                f"Valid: {list(_SESSION_FACTORIES.keys())}"
            )
        if subject != self._subject:
            self._subject = subject
            self._session = None  # Will be recreated on next access

    def next_question(self):
        """Get the next recommended question."""
        session = self._ensure_session()
        return session.next_question()

    def submit_answer(self, student_answer: str) -> AnswerFeedback:
        """Submit an answer for the current question.

        Raises ValueError if no active question.
        """
        session = self._ensure_session()
        return session.submit_answer(student_answer)

    def request_hint(self) -> HintResponse:
        """Request a progressive hint for the current question.

        Raises ValueError if no active question.
        """
        session = self._ensure_session()
        return session.request_hint()

    def get_progress(self) -> Progress:
        """Return a snapshot of current session progress."""
        session = self._ensure_session()
        return session.get_progress()

    def reset(self) -> None:
        """Reset all mastery state and session history."""
        session = self._ensure_session()
        session.reset()
