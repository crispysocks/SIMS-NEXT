"""
AI Tutor -- FastAPI application.

Launch:
    uv run uvicorn app.main:app --reload --port 8000
    # Swagger UI -> http://localhost:8000/docs
"""

import os

from fastapi import FastAPI, Depends, HTTPException, Query

from app.tutor.core.mastery import MasteryStore
from app.tutor.core.recommender import Recommender
from app.tutor.core.session import TutorSession
from app.tutor.schemas import (
    AnswerSubmission,
    AnswerResult,
    DiagnosisResultOut,
    HintResponse,
    KnowledgeSnippetOut,
    MasteryStateOut,
    ProgressOut,
    QuestionOut,
    RemediationPlanOut,
    TutorResponseOut,
    TutoringExplanationOut,
)
from app.tutor.tutor_agent import TutorAgent

SEED = 42

# Default subject when not specified
DEFAULT_SUBJECT = os.environ.get("AI_TUTOR_SUBJECT", "math")


def _create_session(subject: str = DEFAULT_SUBJECT) -> TutorSession:
    agent = TutorAgent(subject_name=subject)
    store = MasteryStore()

    if subject == "english":
        from app.tutor.subjects.english.engine import EnglishQuestionEngine
        from app.tutor.subjects.english.knowledge import PREREQUISITES as ENG_PREREQS
        from app.tutor.rag.factory import create_pipeline

        engine = EnglishQuestionEngine(seed=SEED)
        rec = Recommender(store, prerequisites=ENG_PREREQS)
        pipeline = create_pipeline("english")
        return TutorSession(engine, store, rec, tutor_agent=agent, tutoring_pipeline=pipeline)

    from app.tutor.subjects.math.engine import MathQuestionEngine
    from app.tutor.subjects.math.knowledge import PREREQUISITES

    engine = MathQuestionEngine(seed=SEED)
    rec = Recommender(store, prerequisites=PREREQUISITES)
    return TutorSession(engine, store, rec, tutor_agent=agent)


# Session cache per subject
_sessions: dict[str, TutorSession] = {}


def get_session(subject: str = Query(DEFAULT_SUBJECT, description="Subject: math or english")) -> TutorSession:
    """Dependency: returns the TutorSession for the given subject."""
    global _sessions
    if subject not in _sessions:
        _sessions[subject] = _create_session(subject)
    return _sessions[subject]


app = FastAPI(title="AI Tutor", version="0.3.0")

# -- Startup logging ---------------------------------------------------------

import logging

_log = logging.getLogger("uvicorn")

# Read RAG config for logging
_rag_enabled = os.environ.get("RAG_ENABLED", "false").strip().lower() in ("1", "true", "yes")
_rag_mode = os.environ.get("RAG_RETRIEVER_MODE", "hybrid")
_rag_llm = os.environ.get("RAG_LLM_ENABLED", "true").strip().lower() in ("1", "true", "yes")

_log.info("Default subject: %s", DEFAULT_SUBJECT)
_log.info("RAG enabled: %s", _rag_enabled)
if _rag_enabled:
    _log.info("RAG retriever mode: %s", _rag_mode)
    _log.info("RAG LLM enabled: %s", _rag_llm)


@app.get("/api/question", response_model=QuestionOut)
def next_question(session: TutorSession = Depends(get_session)) -> QuestionOut:
    """Get the next recommended question. Call before POST /api/answer."""
    q = session.next_question()
    return QuestionOut(
        id=q.id,
        subject=q.subject,
        topic=q.topic,
        difficulty=q.difficulty,
        question_text=q.question_text,
        knowledge_tags=q.knowledge_tags,
        learning_objectives=q.learning_objectives,
    )


@app.post("/api/answer", response_model=AnswerResult)
def submit_answer(
    body: AnswerSubmission,
    session: TutorSession = Depends(get_session),
) -> AnswerResult:
    """Submit an answer for the current question. Must call GET /api/question first."""
    try:
        fb = session.submit_answer(body.student_answer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    tr = fb.tutor_response
    return AnswerResult(
        is_correct=fb.is_correct,
        correct_answer=fb.correct_answer,
        student_answer=fb.student_answer,
        topic=fb.topic,
        tutor_response=TutorResponseOut(
            explanation=tr.explanation,
            hint=tr.hint,
            encouragement=tr.encouragement,
        ) if tr else None,
        diagnosis=DiagnosisResultOut(
            error_types=fb.diagnosis.error_types,
            diagnosis_labels=fb.diagnosis.diagnosis_labels,
            confidence=fb.diagnosis.confidence,
        ) if fb.diagnosis else None,
        remediation=RemediationPlanOut(
            recommended_topics=fb.remediation.recommended_topics,
            retrieval_tags=fb.remediation.retrieval_tags,
        ) if fb.remediation else None,
        explanation=TutoringExplanationOut(
            what_is_wrong=fb.explanation.what_is_wrong,
            why_it_is_wrong=fb.explanation.why_it_is_wrong,
            how_to_fix=fb.explanation.how_to_fix,
            similar_examples=fb.explanation.similar_examples,
            retrieved_context=fb.explanation.retrieved_context,
            generation_source=fb.explanation.metadata.get("source"),
            metadata=fb.explanation.metadata,
        ) if fb.explanation else None,
        retrieved_snippets=[
            KnowledgeSnippetOut(
                id=s.id,
                title=s.title,
                topic=s.topic,
                tags=s.tags,
                diagnosis_labels=s.diagnosis_labels,
                score=s.score,
                metadata=s.metadata,
            )
            for s in fb.knowledge_snippets
        ],
    )


@app.post("/api/hint", response_model=HintResponse)
def request_hint(session: TutorSession = Depends(get_session)) -> HintResponse:
    """Request a progressive hint for the current question. Up to 3 levels."""
    try:
        return session.request_hint()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/mastery", response_model=list[MasteryStateOut])
def get_mastery(
    session: TutorSession = Depends(get_session),
) -> list[MasteryStateOut]:
    """Return current mastery for all topics."""
    states = session.get_progress().mastery_states
    return [
        MasteryStateOut(
            topic_id=s.topic_id,
            alpha=s.alpha,
            beta=s.beta,
            total_attempts=s.total_attempts,
            correct_attempts=s.correct_attempts,
            last_seen=s.last_seen,
            mastery=s.mastery,
            variance=s.variance,
        )
        for s in states
    ]


@app.get("/api/progress", response_model=ProgressOut)
def get_progress(
    session: TutorSession = Depends(get_session),
) -> ProgressOut:
    """Return full session progress snapshot."""
    p = session.get_progress()
    return ProgressOut(
        mastery_states=[
            MasteryStateOut(
                topic_id=s.topic_id,
                alpha=s.alpha,
                beta=s.beta,
                total_attempts=s.total_attempts,
                correct_attempts=s.correct_attempts,
                last_seen=s.last_seen,
                mastery=s.mastery,
                variance=s.variance,
            )
            for s in p.mastery_states
        ],
        total_questions=p.total_questions,
        correct_count=p.correct_count,
        accuracy=p.accuracy,
        correct_streak=p.correct_streak,
        wrong_streak=p.wrong_streak,
    )


@app.post("/api/reset")
def reset(session: TutorSession = Depends(get_session)) -> dict:
    """Reset all mastery state and session history."""
    session.reset()
    return {"status": "ok"}
