"""统一定义的指标体系函数——纯 Python 计算，可独立单元测试。

每个函数输入单个班级或多班级的数值序列，返回计算后的指标值。
"""

import math
from collections import Counter


def kp_mastery_rate(scores: list[float], max_scores: list[float]) -> float:
    """知识点掌握率：该知识点所有题目得分之和 / 满分之和。"""
    total_score = sum(scores)
    total_max = sum(max_scores)
    return total_score / total_max if total_max > 0 else 0.0


def class_avg(scores: list[float]) -> float:
    """班级均分。"""
    return sum(scores) / len(scores) if scores else 0.0


def grade_avg(all_class_scores: list[float]) -> float:
    """年级均分。"""
    return sum(all_class_scores) / len(all_class_scores) if all_class_scores else 0.0


def class_deviation(class_score: float, grade_score: float) -> float:
    """班级偏差：班级值 - 年级值。正值表示高于年级平均。"""
    return class_score - grade_score


def std_dev(values: list[float]) -> float:
    """标准差——衡量班级内成绩离散程度。"""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def discrimination_index(
    scores: list[float], max_scores: list[float], top_n: int = 20
) -> float:
    """区分度指数——高分组得分率 - 低分组得分率。

    按得分率排序，取前 top_n% 和后 top_n% 计算差值。
    返回值范围 [-1, 1]，> 0.4 为优秀，< 0.2 为低质量。
    """
    if len(scores) < 5:
        return 0.0

    # 计算每个学生的得分率并排序
    rates = sorted(s / m for s, m in zip(scores, max_scores))
    n = max(1, int(len(rates) * top_n / 100))

    high_group = rates[-n:]
    low_group = rates[:n]

    high_rate = sum(high_group) / len(high_group)
    low_rate = sum(low_group) / len(low_group)

    return high_rate - low_rate


def difficulty_coefficient(scores: list[float], max_scores: list[float]) -> float:
    """实际难度系数——1 - 平均得分率。0=容易，1=困难。"""
    rate = kp_mastery_rate(scores, max_scores)
    return 1.0 - rate


def tier_thresholds(ranked_scores: list[float]) -> dict[str, float]:
    """根据排名百分比计算四层阈值。

    A 层: 前 25%, B 层: 25%-50%, C 层: 50%-75%, D 层: 后 25%。
    """
    if not ranked_scores:
        return {"A_min": 0, "B_min": 0, "C_min": 0}

    sorted_scores = sorted(ranked_scores, reverse=True)
    n = len(sorted_scores)

    return {
        "A_min": sorted_scores[max(0, int(n * 0.25) - 1)],
        "B_min": sorted_scores[max(0, int(n * 0.50) - 1)],
        "C_min": sorted_scores[max(0, int(n * 0.75) - 1)],
    }


def enrollment_rate(scores: list[float], target_line: float) -> float:
    """上线率——达到目标分的学生比例。"""
    if not scores:
        return 0.0
    passed = sum(1 for s in scores if s >= target_line)
    return passed / len(scores)


def trend_slope(exam_avgs: list[float]) -> float:
    """趋势斜率——简单线性回归 (x: 考试序号 0..n-1, y: 均分)。

    返回斜率，正值上升趋势，负值下降趋势。
    """
    n = len(exam_avgs)
    if n < 2:
        return 0.0

    x_mean = (n - 1) / 2
    y_mean = sum(exam_avgs) / n

    numerator = sum((i - x_mean) * (exam_avgs[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    return numerator / denominator if denominator != 0 else 0.0
