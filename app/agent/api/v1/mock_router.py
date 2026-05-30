"""Mock 数据 API——通过 HTTP 接口管理模拟数据生成与清理。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.agent.mock.cli import cmd_generate, cmd_clean, cmd_stats
from app.agent.models.subject import Subject
from app.agent.models.knowledge_point import KnowledgePoint
from app.agent.models.exam import Exam
from app.agent.models.question import Question
from app.agent.models.score_record import ScoreRecord

router = APIRouter(prefix="/mock", tags=["agent-mock"])


class GenerateRequest(BaseModel):
    classes: int = Field(default=3, ge=1, le=10)
    students: int = Field(default=5, ge=1, le=200)
    exams: int = Field(default=6, ge=1, le=12)


class MockArgs:
    """适配 CLI 的参数对象。"""
    classes: int = 3
    students: int = 5
    exams: int = 6


@router.post("/generate", status_code=201)
def generate_mock_data(req: GenerateRequest, db: Session = Depends(get_db)):
    """通过 API 生成全套 Mock 数据。"""
    args = MockArgs()
    args.classes = req.classes
    args.students = req.students
    args.exams = req.exams
    cmd_generate(args)
    return {"status": "ok", "message": f"已生成 {req.classes} 个班级 × {req.students} 人 × {req.exams} 场考试的 Mock 数据"}


@router.delete("/clean", status_code=200)
def clean_mock_data(db: Session = Depends(get_db)):
    """清空所有 agent 表数据。"""
    args = MockArgs()
    cmd_clean(args)
    return {"status": "ok", "message": "已清空所有 agent 表"}


@router.get("/stats")
def get_mock_stats(db: Session = Depends(get_db)):
    """查看当前数据统计。"""
    return {
        "subjects": db.query(Subject).count(),
        "knowledge_points": db.query(KnowledgePoint).count(),
        "exams": db.query(Exam).count(),
        "questions": db.query(Question).count(),
        "score_records": db.query(ScoreRecord).count(),
    }
