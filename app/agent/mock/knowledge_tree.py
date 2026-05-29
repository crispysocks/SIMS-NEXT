"""知识点树 + 依赖关系 + 题目 Mock 数据生成器。

生成约 30 个知识点（三级树：5 章 → 15 节 → 30 知识点）
+ 知识点间依赖 DAG（约 15 条边）
+ 144 道题目（6 次考试 × 24 题/次）
"""

import random


# ── 知识点树定义 ──────────────────────────────────

KNOWLEDGE_TREE_DEF = {
    "代数基础": {
        "sort_order": 1,
        "sections": {
            "数与式": {
                "sort_order": 1,
                "points": [
                    "有理数运算", "整式加减", "整式乘除与因式分解",
                ],
            },
            "方程与不等式": {
                "sort_order": 2,
                "points": [
                    "一元一次方程", "二元一次方程组", "一元一次不等式",
                ],
            },
        },
    },
    "几何图形": {
        "sort_order": 2,
        "sections": {
            "线与角": {
                "sort_order": 1,
                "points": [
                    "线段与角的概念", "相交线与平行线",
                ],
            },
            "三角形": {
                "sort_order": 2,
                "points": [
                    "三角形基本性质", "全等三角形", "相似三角形",
                ],
            },
            "四边形": {
                "sort_order": 3,
                "points": [
                    "平行四边形", "特殊平行四边形", "梯形",
                ],
            },
        },
    },
    "函数分析": {
        "sort_order": 3,
        "sections": {
            "平面直角坐标系": {
                "sort_order": 1,
                "points": [
                    "坐标与图形变换", "函数概念与表示",
                ],
            },
            "一次函数与反比例": {
                "sort_order": 2,
                "points": [
                    "一次函数图像与性质", "反比例函数图像与性质",
                ],
            },
            "二次函数": {
                "sort_order": 3,
                "points": [
                    "二次函数图像与性质", "二次函数与实际问题",
                ],
            },
        },
    },
    "概率统计": {
        "sort_order": 4,
        "sections": {
            "数据统计": {
                "sort_order": 1,
                "points": [
                    "数据的收集与整理", "统计图表", "平均数中位数众数",
                ],
            },
            "概率初步": {
                "sort_order": 2,
                "points": [
                    "事件与可能性", "概率计算",
                ],
            },
        },
    },
    "综合应用": {
        "sort_order": 5,
        "sections": {
            "几何综合": {
                "sort_order": 1,
                "points": [
                    "勾股定理", "解直角三角形",
                ],
            },
            "代数与几何综合": {
                "sort_order": 2,
                "points": [
                    "函数与几何综合", "方程与几何综合",
                ],
            },
        },
    },
}


def generate_knowledge_tree(subject_id: int = 1) -> list[dict]:
    """生成知识点树，返回按层级排序的列表。

    Returns:
        [{id, name, level, parent_id, sort_order, core_weight, subject_id}]
    """
    kps = []
    kp_id = 0

    for chapter_name, chapter_def in KNOWLEDGE_TREE_DEF.items():
        kp_id += 1
        kps.append({
            "id": kp_id,
            "name": chapter_name,
            "level": 1,
            "parent_id": None,
            "sort_order": chapter_def["sort_order"],
            "core_weight": 1.0,
            "subject_id": subject_id,
        })
        chapter_id = kp_id

        for section_name, section_def in chapter_def["sections"].items():
            kp_id += 1
            kps.append({
                "id": kp_id,
                "name": section_name,
                "level": 2,
                "parent_id": chapter_id,
                "sort_order": section_def["sort_order"],
                "core_weight": 1.0,
                "subject_id": subject_id,
            })
            section_id = kp_id

            for point_name in section_def["points"]:
                kp_id += 1
                kps.append({
                    "id": kp_id,
                    "name": point_name,
                    "level": 3,
                    "parent_id": section_id,
                    "sort_order": len(kps),
                    "core_weight": round(random.uniform(0.7, 1.5), 2),
                    "subject_id": subject_id,
                })

    return kps


# ── 依赖关系 DAG 定义 ────────────────────────────

DEPENDENCY_DEF = [
    # (source, target) — source 是 target 的前置知识
    ("整式加减", "整式乘除与因式分解"),
    ("整式加减", "一元一次方程"),
    ("一元一次方程", "二元一次方程组"),
    ("一元一次方程", "一元一次不等式"),
    ("一元一次方程", "一次函数图像与性质"),
    ("线段与角的概念", "相交线与平行线"),
    ("三角形基本性质", "全等三角形"),
    ("三角形基本性质", "相似三角形"),
    ("全等三角形", "平行四边形"),
    ("平行四边形", "特殊平行四边形"),
    ("坐标与图形变换", "一次函数图像与性质"),
    ("一次函数图像与性质", "二次函数图像与性质"),
    ("整式乘除与因式分解", "二次函数图像与性质"),
    ("数据的收集与整理", "统计图表"),
    ("数据的收集与整理", "平均数中位数众数"),
    ("三角形基本性质", "勾股定理"),
    ("勾股定理", "解直角三角形"),
    ("相似三角形", "函数与几何综合"),
    ("二次函数图像与性质", "函数与几何综合"),
    ("整式加减", "方程与几何综合"),
    ("一元一次方程", "方程与几何综合"),
]


def generate_dependencies(kps: list[dict]) -> list[dict]:
    """基于知识点名称匹配依赖关系。

    Returns:
        [{source_kp_id, target_kp_id, dependency_weight}]
    """
    name_to_id = {kp["name"]: kp["id"] for kp in kps}
    deps = []

    for source_name, target_name in DEPENDENCY_DEF:
        if source_name in name_to_id and target_name in name_to_id:
            deps.append({
                "source_kp_id": name_to_id[source_name],
                "target_kp_id": name_to_id[target_name],
                "dependency_weight": round(random.uniform(0.5, 1.0), 2),
            })

    return deps


# ── 题目生成 ─────────────────────────────────────

QUESTION_TYPES = ["选择题", "填空题", "解答题", "证明题"]


def generate_questions(
    exam_ids: list[int],
    kps: list[dict],
    questions_per_exam: int = 24,
    seed: int | None = None,
) -> list[dict]:
    """为每场考试生成题目及知识点关联。

    每道题 1-3 个关联知识点（level=3 的知识点）。

    Returns:
        [
            {id, exam_id, title, question_type, difficulty, max_score, sort_order,
             kps: [{kp_id, relevance}]}
        ]
    """
    if seed is not None:
        random.seed(seed)

    leaf_kps = [kp for kp in kps if kp["level"] == 3]
    questions = []
    qid = 0

    for exam_id in exam_ids:
        # 每场考试的题型分布
        type_dist = ["选择题"] * 10 + ["填空题"] * 6 + ["解答题"] * 6 + ["证明题"] * 2

        for i in range(questions_per_exam):
            qid += 1
            q_type = type_dist[i % len(type_dist)]

            # 题目难度分布（大部分中等难度）
            if q_type == "选择题":
                difficulty = round(random.uniform(0.2, 0.75), 2)
                max_score = random.choice([3, 4, 5])
            elif q_type == "填空题":
                difficulty = round(random.uniform(0.3, 0.80), 2)
                max_score = random.choice([3, 5])
            elif q_type == "解答题":
                difficulty = round(random.uniform(0.4, 0.90), 2)
                max_score = random.choice([8, 10, 12])
            else:  # 证明题
                difficulty = round(random.uniform(0.5, 0.95), 2)
                max_score = random.choice([8, 10, 12])

            # 关联 1-3 个知识点
            kp_count = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
            selected_kps = random.sample(leaf_kps, min(kp_count, len(leaf_kps)))

            title = _generate_question_title(kp_count, selected_kps)

            questions.append({
                "id": qid,
                "exam_id": exam_id,
                "title": title,
                "question_type": q_type,
                "difficulty": difficulty,
                "max_score": max_score,
                "sort_order": i + 1,
                "kps": [{"kp_id": kp["id"], "relevance": round(random.uniform(0.6, 1.0), 2)}
                        for kp in selected_kps],
            })

    return questions


def _generate_question_title(kp_count: int, selected_kps: list[dict]) -> str:
    """生成模拟题目标题。"""
    prefixes = ["已知", "设", "计算", "证明", "求解", "如图所示，"]
    kp_names = [kp["name"] for kp in selected_kps]
    kp_str = "与".join(kp_names)

    if kp_count == 1:
        return f"{random.choice(prefixes)}{kp_str}相关题目"
    else:
        return f"{random.choice(prefixes)}{kp_str}，求综合解答"
