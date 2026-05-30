"""AI Tutor API router — thin endpoints delegating to TutorService."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.tutor_service import TutorService
from app.schemas.tutor import (
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

router = APIRouter(prefix="/tutor", tags=["tutor"])

# Module-level singleton service (in-memory, no DB dependency)
_service = TutorService()


def get_tutor_service() -> TutorService:
    return _service


class SubjectSwitch(BaseModel):
    """Request model for switching subjects."""
    subject: str


class SubjectInfo(BaseModel):
    """Response model for subject info."""
    subject: str
    available_subjects: list[str]


@router.get("/question", response_model=QuestionOut)
def next_question(
    service: TutorService = Depends(get_tutor_service),
) -> QuestionOut:
    """Get the next recommended question. Call before POST /answer."""
    q = service.next_question()
    return QuestionOut(
        id=q.id,
        subject=q.subject,
        topic=q.topic,
        difficulty=q.difficulty,
        question_text=q.question_text,
        knowledge_tags=q.knowledge_tags,
        learning_objectives=q.learning_objectives,
    )


@router.post("/answer", response_model=AnswerResult)
def submit_answer(
    body: AnswerSubmission,
    service: TutorService = Depends(get_tutor_service),
) -> AnswerResult:
    """Submit an answer for the current question. Must call GET /question first."""
    try:
        fb = service.submit_answer(body.student_answer)
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


@router.post("/hint", response_model=HintResponse)
def request_hint(
    service: TutorService = Depends(get_tutor_service),
) -> HintResponse:
    """Request a progressive hint for the current question. Up to 3 levels."""
    try:
        return service.request_hint()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mastery", response_model=list[MasteryStateOut])
def get_mastery(
    service: TutorService = Depends(get_tutor_service),
) -> list[MasteryStateOut]:
    """Return current mastery for all topics."""
    states = service.get_progress().mastery_states
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


@router.get("/progress", response_model=ProgressOut)
def get_progress(
    service: TutorService = Depends(get_tutor_service),
) -> ProgressOut:
    """Return full session progress snapshot."""
    p = service.get_progress()
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


@router.post("/reset")
def reset(
    service: TutorService = Depends(get_tutor_service),
) -> dict:
    """Reset all mastery state and session history."""
    service.reset()
    return {"status": "ok"}


@router.get("/subject", response_model=SubjectInfo)
def get_subject(
    service: TutorService = Depends(get_tutor_service),
) -> SubjectInfo:
    """Get current subject and available subjects."""
    return SubjectInfo(
        subject=service.subject,
        available_subjects=["math", "english"],
    )


@router.post("/subject", response_model=SubjectInfo)
def switch_subject(
    body: SubjectSwitch,
    service: TutorService = Depends(get_tutor_service),
) -> SubjectInfo:
    """Switch to a different subject. Resets the session."""
    try:
        service.switch_subject(body.subject)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SubjectInfo(
        subject=service.subject,
        available_subjects=["math", "english"],
    )
