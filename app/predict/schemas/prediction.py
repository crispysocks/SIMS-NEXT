from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AdmissionType(str, Enum):
    STRETCH = "冲刺"      # <40%
    STABLE = "稳定"      # 40%~75%
    SECURE = "保底"       # >75%


class TierLevel(str, Enum):
    L1 = "职业教育"       # 难度系数 0.20
    L2 = "普通高中"       # 难度系数 0.50
    L3 = "重点高中"       # 难度系数 0.80
    L4 = "顶级高中"       # 难度系数 1.00


class PredictionItem(BaseModel):
    school_name: str
    predicted_score: float
    admission_probability: int
    admission_type: str
    score_diff: int = 0  # 学生分数 - 学校预测分数


class StudentPrediction(BaseModel):
    student_id: int
    current_score: float
    current_ranking: int
    predicted_ranking: int
    ranking_trend: str
    predictions: dict[str, list[PredictionItem]]


class WhatIfResult(BaseModel):
    subject: str
    score_increase: int
    key_high_school_probability_change: str
    ranking_improvement: str