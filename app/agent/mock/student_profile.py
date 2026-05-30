"""学生画像参数生成器——基于随机参数生成模拟学生画像。

6 维度参数:
- base_level: 基础水平 (0-100)，影响所有科目得分
- learning_speed: 学习速度 (-1 到 1)，影响跨考试进步幅度
- memory_retention: 记忆保持率 (0.3-1.0)，影响已学知识点稳定性
- exam_stability: 考试稳定性 (0.3-1.0)，影响随机波动幅度
- careless_prob: 粗心概率 (0.01-0.15)，影响简单题失分
- topic_affinity: 不同知识点的亲和度偏差 (dict)
"""

import random
import math


def generate_student_profiles(
    class_id: int, count: int = 5, seed: int | None = None
) -> list[dict]:
    """为指定班级生成 N 个学生画像。

    Args:
        class_id: 班级 ID（1-3）
        count: 每个班级的学生数
        seed: 随机种子（用于复现）

    Returns:
        [{student_no, name, class_id, profile: {6 dims}}, ...]
    """
    if seed is not None:
        random.seed(seed + class_id * 1000)

    # 班级平均基础水平有所差异，模拟好班/普通班
    class_avg = {1: 68, 2: 58, 3: 52}.get(class_id, 58)
    class_std = 14

    profiles = []
    for i in range(1, count + 1):
        student_no = f"S{class_id:02d}{i:03d}"
        name = _generate_name(i, class_id)

        base = max(10, min(98, round(random.gauss(class_avg, class_std), 1)))
        learning_speed = round(random.uniform(-0.8, 1.0), 3)
        memory_retention = round(random.uniform(0.35, 0.98), 3)
        exam_stability = round(random.uniform(0.3, 0.95), 3)
        careless_prob = round(random.uniform(0.02, 0.14), 3)

        # 不同知识模块的亲和度（共 5 大模块）
        topic_affinity = {
            "代数基础": round(random.gauss(0, 0.25), 3),
            "几何图形": round(random.gauss(0, 0.25), 3),
            "函数分析": round(random.gauss(0, 0.25), 3),
            "概率统计": round(random.gauss(0, 0.25), 3),
            "综合应用": round(random.gauss(0, 0.25), 3),
        }

        age = random.randint(13, 15)
        enrollment_date = "2025-09-01"

        profiles.append({
            "student_no": student_no,
            "name": name,
            "gender": "男" if i % 2 == 0 else "女",
            "age": age,
            "class_id": class_id,
            "enrollment_date": enrollment_date,
            "profile": {
                "base_level": base,
                "learning_speed": learning_speed,
                "memory_retention": memory_retention,
                "exam_stability": exam_stability,
                "careless_prob": careless_prob,
                "topic_affinity": topic_affinity,
            },
        })

    return profiles


def _generate_name(index: int, class_id: int = 0) -> str:
    """生成中文姓名（从常见姓氏+名字中选取）。"""
    surnames = [
        "张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
        "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗",
        "郑", "梁", "谢", "宋", "唐", "韩", "曹", "许", "邓", "冯",
        "彭", "曾", "萧", "田", "董", "潘", "袁", "于", "蒋", "蔡",
        "余", "杜", "叶", "程", "苏", "魏", "吕", "丁", "任", "沈",
        "姚", "卢", "姜", "崔", "钟", "谭", "陆", "汪", "范", "金",
        "石", "廖", "贾", "夏", "韦", "付", "方", "白", "邹", "孟",
        "熊", "秦", "邱", "江", "尹", "薛", "闫", "段", "雷", "侯",
    ]
    given_chars = [
        "伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "洋", "艳",
        "勇", "军", "杰", "娟", "涛", "明", "超", "秀英", "华", "慧",
        "鑫", "桂英", "建华", "玲", "建国", "建军", "志强", "文博",
        "雪", "飞", "斌", "宇", "浩", "然", "博", "文", "毅", "恒",
        "思", "雨", "欣", "子涵", "梓", "辰", "泽", "瑞", "佳", "怡",
        "悦", "诗", "琪", "瑜", "婉", "娴", "雅", "清", "岚", "若",
    ]
    offset = index + class_id * 100
    surname = surnames[(offset * 17) % len(surnames)]
    given = given_chars[(offset * 31) % len(given_chars)]
    return surname + given
