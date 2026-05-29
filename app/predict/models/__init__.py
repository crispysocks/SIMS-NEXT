# Models
from app.predict.models.exam_record import ExamRecord
from app.predict.models.high_school import HighSchool
from app.predict.models.admission_line import AdmissionScoreLine
from app.predict.models.chat_session import ChatSession
from app.predict.models.student_portrait import StudentPortrait
from app.predict.models.score_rank_line import ScoreRankLine

__all__ = [
    "ExamRecord",
    "HighSchool",
    "AdmissionScoreLine",
    "ChatSession",
    "StudentPortrait",
    "ScoreRankLine",
]