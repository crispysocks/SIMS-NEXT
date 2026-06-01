


from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from app.core.database import get_db
from app.predict.services.portrait_service import PortraitService
from app.predict.services.prediction_service import PredictionService
from app.predict.services.risk_service import RiskService
from app.predict.services.chat_service import ChatService
from app.predict.services.trace_service import get_trace_service
from app.predict.schemas.advice import AIAdvice, SubjectAdvice
from app.predict.schemas.chat import ChatRequest, ChatStreamEvent
from app.predict.repositories.exam_record_repository import ExamRecordRepository

router = APIRouter(prefix="/advice", tags=["AI建议"])


def _generate_suggestions(portrait, prediction, risk, records) -> list:
    """根据学生实际数据生成针对性建议"""
    suggestions = []

    # 1. 分析各科目平均分，找出最弱科目
    subject_scores = {}
    for r in records:
        if r.subject not in subject_scores:
            subject_scores[r.subject] = []
        subject_scores[r.subject].append(float(r.score))

    subject_avgs = {s: sum(scores)/len(scores) for s, scores in subject_scores.items() if scores}
    if subject_avgs:
        weakest = min(subject_avgs, key=subject_avgs.get)
        weakest_score = subject_avgs[weakest]

        if weakest_score < 60:
            advice = f"{weakest}基础薄弱，建议每天30分钟专项训练，从基础题抓起"
            improvement = "+15-20分"
        elif weakest_score < 75:
            advice = f"{weakest}有一定提升空间，建议针对重点章节强化练习"
            improvement = "+8-10分"
        else:
            advice = f"{weakest}保持稳定，注意查漏补缺"
            improvement = "+5分"

        suggestions.append(SubjectAdvice(subject=weakest, advice=advice, expected_improvement=improvement))

    # 2. 根据排名趋势给出建议
    if prediction.ranking_trend == "下降":
        suggestions.append(SubjectAdvice(
            subject="综合",
            advice="排名呈下降趋势，需要分析原因：是基础不牢还是考试状态问题？建议近期专注巩固基础",
            expected_improvement="--"
        ))
    elif prediction.ranking_trend == "上升":
        suggestions.append(SubjectAdvice(
            subject="综合",
            advice="排名稳步上升，说明学习方法有效，建议保持当前节奏，稳扎稳打",
            expected_improvement="持续提升"
        ))

    # 3. 根据风险标签给出建议
    if risk.risk_tags:
        for tag in risk.risk_tags[:2]:
            subject = tag.replace("波动", "").replace("下滑", "")
            if "下滑" in tag:
                suggestions.append(SubjectAdvice(
                    subject=subject,
                    advice=f"{subject}成绩下滑，需要立即重视，建议分析最近3次考试失分原因",
                    expected_improvement="+5-10分"
                ))
            elif "波动" in tag:
                suggestions.append(SubjectAdvice(
                    subject=subject,
                    advice=f"{subject}成绩波动大，建议加强该科目基础训练，减少失误率",
                    expected_improvement="+3-8分"
                ))

    # 4. 稳定型学生建议
    if portrait.learning_type == "波动型":
        suggestions.append(SubjectAdvice(
            subject="综合",
            advice="成绩波动较大，建议建立错题本，分析每次考试失误原因",
            expected_improvement="+5分"
        ))

    return suggestions[:5]


@router.get("/{student_id}", response_model=AIAdvice)
def get_ai_advice(student_id: int, db: Session = Depends(get_db)):
    portrait_service = PortraitService(db)
    prediction_service = PredictionService(db)
    risk_service = RiskService(db)

    portrait = portrait_service.analyze_student(student_id)
    if not portrait:
        raise HTTPException(status_code=404, detail="学生画像不存在")

    exam_repo = ExamRecordRepository(db)
    latest_records = exam_repo.get_latest_by_student(student_id)
    if not latest_records:
        raise HTTPException(status_code=404, detail="无考试成绩数据")

    latest_exam_name = latest_records[0].exam_name
    latest_exam_records = [r for r in latest_records if r.exam_name == latest_exam_name]
    current_score = sum(float(r.score) for r in latest_exam_records)
    prediction = prediction_service.predict_student_admission(student_id, current_score)
    risk = risk_service.analyze_risk(student_id)

    if not prediction.predictions:
        raise HTTPException(status_code=404, detail="无升学预测数据")

    # Determine tier from predictions
    all_predictions = []
    for category in ["冲刺", "稳定", "保底"]:
        all_predictions.extend(prediction.predictions.get(category, []))

    current_tier = "L2"
    target_tier = "L3"
    if all_predictions:
        stretch_count = len(prediction.predictions.get("冲刺", []))
        secure_count = len(prediction.predictions.get("保底", []))
        if secure_count > stretch_count:
            current_tier = "L3"
            target_tier = "L4"
        elif stretch_count > secure_count:
            current_tier = "L1"
            target_tier = "L2"

    # 生成针对性建议
    suggestions = _generate_suggestions(portrait, prediction, risk, latest_exam_records)

    return AIAdvice(
        current_tier=current_tier,
        target_tier=target_tier,
        suggestions=suggestions,
        overall_expected_improvement="+15-20分"
    )


@router.post("/{student_id}/chat")
async def chat_advice(
    student_id: int,
    request: ChatRequest = Body(...),
    db: Session = Depends(get_db)
):
    """SSE流式Chat接口"""
    chat_service = ChatService(db)

    def event_generator():
        for event in chat_service.chat(student_id, request.message):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/{student_id}/debug")
def get_chat_debug(student_id: int):
    """获取上次chat的思考过程trace"""
    trace = get_trace_service()
    steps = trace.get_steps()

    return {
        "student_id": student_id,
        "steps": [s.to_dict() for s in steps],
        "step_count": len(steps)
    }