"""
AI Math Tutor — FastAPI application.

Launch:
    uv run uvicorn app.main:app --reload --port 8000
    # Swagger UI → http://localhost:8000/docs
"""

from fastapi import FastAPI, Depends, HTTPException

from app.engine import QuestionEngine
from app.mastery import MasteryStore
from app.recommender import Recommender
from app.schemas import (
    AnswerSubmission,
    AnswerResult,
    HintResponse,
    MasteryStateOut,
    ProgressOut,
    QuestionOut,
    TutorResponseOut,
)
from app.session import TutorSession
from app.tutor_agent import TutorAgent

SEED = 42


def _create_session() -> TutorSession:
    engine = QuestionEngine(seed=SEED)
    store = MasteryStore()
    rec = Recommender(store)
    agent = TutorAgent()
    return TutorSession(engine, store, rec, tutor_agent=agent)


_session: TutorSession | None = None


def get_session() -> TutorSession:
    """Dependency: returns the singleton TutorSession."""
    global _session
    if _session is None:
        _session = _create_session()
    return _session


app = FastAPI(title="AI Math Tutor", version="0.1.0")


@app.get("/api/question", response_model=QuestionOut)
def next_question(session: TutorSession = Depends(get_session)) -> QuestionOut:
    """Get the next recommended question. Call before POST /api/answer."""
    q = session.next_question()
    return QuestionOut(
        id=q.id,
        topic=q.topic,
        difficulty=q.difficulty,
        question_text=q.question_text,
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
