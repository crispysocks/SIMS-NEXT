"""成绩生成器——基于学生画像 × 知识点 × 题目参数模拟真实成绩。

核心逻辑:
1. 对每个学生，计算其对每道题的"真实力得分率"
2. 根据考试稳定性注入随机波动
3. 根据粗心概率对简单题做额外扣分
4. 跨考试体现学习进步/退步趋势
"""

import random
import math
from datetime import date, timedelta


def generate_scores(
    profiles: list[dict],
    questions: list[dict],
    kps: list[dict],
    exams: list[dict],
    seed: int | None = None,
) -> list[dict]:
    """生成所有成绩记录。

    Args:
        profiles: 学生画像列表
        questions: 题目列表 [{id, exam_id, difficulty, max_score, kps: [{kp_id, relevance}]}]
        kps: 知识点列表 [{id, name, level, parent_id}]
        exams: 考试列表 [{id, exam_date, ...}]
        seed: 随机种子

    Returns:
        [{student_no, exam_id, question_id, score, max_score}]
    """
    if seed is not None:
        random.seed(seed)

    # 建立辅助索引
    kp_id_to_chapter = {}
    for kp in kps:
        if kp["level"] == 3:
            # 找该知识点所属章节
            parent = _find_parent(kps, kp["parent_id"])
            if parent:
                grandparent = _find_parent(kps, parent["parent_id"])
                if grandparent:
                    kp_id_to_chapter[kp["id"]] = grandparent["name"]

    # 按考试排序
    exams_sorted = sorted(exams, key=lambda e: e["exam_date"])

    # 按 class_id 建立考试索引
    exams_by_class: dict[int, list[dict]] = {}
    for exam in exams:
        cid = exam.get("class_id", 0)
        exams_by_class.setdefault(cid, []).append(exam)

    records = []
    for student in profiles:
        p = student["profile"]
        student_class = student["class_id"]
        class_exams = exams_by_class.get(student_class, [])
        for exam_idx, exam in enumerate(class_exams):
            exam_questions = [q for q in questions if q["exam_id"] == exam["id"]]
            for q in exam_questions:
                score = _compute_score(student, q, p, kp_id_to_chapter, exam_idx)
                records.append({
                    "student_no": student["student_no"],
                    "exam_id": exam["id"],
                    "question_id": q["id"],
                    "score": score,
                    "max_score": q["max_score"],
                })

    return records


def _find_parent(kps: list[dict], parent_id: int | None) -> dict | None:
    if parent_id is None:
        return None
    for kp in kps:
        if kp["id"] == parent_id:
            return kp
    return None


def _compute_score(
    student: dict,
    question: dict,
    profile: dict,
    kp_id_to_chapter: dict[int, str],
    exam_idx: int,
) -> float:
    """计算单个学生的单题得分。"""

    # 1. 基础实力得分率 = base_level 映射到 0-1 + 知识点亲和度
    base_rate = profile["base_level"] / 100.0

    # 知识点亲和度加权
    affinity_sum = 0
    for kp_ref in question.get("kps", []):
        kp_id = kp_ref["kp_id"]
        chapter = kp_id_to_chapter.get(kp_id, "")
        affinity = profile["topic_affinity"].get(chapter, 0)
        affinity_sum += affinity
    avg_affinity = affinity_sum / max(len(question.get("kps", [])), 1)

    # 题目难度影响
    difficulty_penalty = question["difficulty"] * 0.6  # 难度的实际影响系数

    # 综合实力得分率
    ability_rate = base_rate + avg_affinity - difficulty_penalty + 0.1

    # 2. 按考试序号体现学习进步/退步
    learning_delta = profile["learning_speed"] * exam_idx * 0.015
    ability_rate += learning_delta

    # 3. 记忆保持率影响已学知识点的稳定性
    ability_rate *= (0.7 + 0.3 * profile["memory_retention"])

    # 4. 考试随机波动 (正态分布噪声)
    stability = 1.0 - profile["exam_stability"]
    noise = random.gauss(0, stability * 0.18)
    ability_rate += noise

    # 5. 粗心惩罚（对简单题）
    if question["difficulty"] < 0.35:
        if random.random() < profile["careless_prob"] * 2:
            ability_rate -= random.uniform(0.1, 0.35)

    # 6. 限制得分率在合理范围
    ability_rate = max(0.02, min(1.0, ability_rate))

    # 7. 计算实际得分
    raw_score = ability_rate * question["max_score"]

    # 将得分离散化到合适精度
    if question["max_score"] <= 5:
        return round(raw_score) if random.random() < 0.7 else round(raw_score + random.uniform(-0.5, 0.5))
    else:
        return max(0, round(raw_score * 2) / 2)


def generate_exams(
    class_ids: list[int],
    subject_id: int = 1,
    exam_count: int = 6,
    start_date: date | None = None,
) -> list[dict]:
    """为多个班级生成考试记录。

    考试间隔约 25-35 天，覆盖一个完整学期。
    """
    if start_date is None:
        start_date = date(2025, 9, 1)

    exam_types = ["入学摸底", "第一次月考", "期中考试", "第二次月考", "第三次月考", "期末考试"]
    exams = []
    eid = 0

    for class_id in class_ids:
        for i in range(exam_count):
            eid += 1
            exam_date = start_date + timedelta(days=i * random.randint(26, 35) + random.randint(0, 5))
            exams.append({
                "id": eid,
                "class_id": class_id,
                "subject_id": subject_id,
                "name": f"初三({class_id})班{exam_types[i % len(exam_types)]}",
                "exam_date": exam_date,
                "exam_type": exam_types[i % len(exam_types)],
                "semester": "2025上",
                "total_score": 100,
            })

    return exams
