"""Generate mock data for agent tables based on existing SIMS data.

Inserts 11 agent tables with data consistent with students/teachers/classes/scores.
Run: uv run python scripts/seed_agent_data.py
"""

import random
from datetime import date
from sqlalchemy import text
from app.core.database import engine, SessionLocal

random.seed(42)
db = SessionLocal()

# ── Existing data summary ──────────────────────────────────
# 10 students: S2026001-S2026010
#   Class 1 (id=1): S2026001, S2026002, S2026004, S2026007, S2026008 (5人)
#   Class 2 (id=2): S2026003, S2026010 (2人)
#   Class 3 (id=3): S2026005, S2026006, S2026009 (3人)
# 3 classes: 初三(1)班, 初三(2)班, 初三(3)班

print("Clearing existing agent data...")
db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
tables = [
    "agent_score_records", "agent_question_kps", "agent_tool_calls",
    "agent_messages", "agent_analysis_data", "agent_questions",
    "agent_knowledge_dependencies", "agent_knowledge_points",
    "agent_exams", "agent_sessions", "agent_subjects",
]
for t in tables:
    db.execute(text(f"TRUNCATE TABLE {t}"))
db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
db.commit()

# ── 1. agent_subjects ─────────────────────────────────────
print("Inserting agent_subjects...")
db.execute(
    text("INSERT INTO agent_subjects (id, name, grade_level, description) "
         "VALUES (:id, :name, :grade, :desc)"),
    {"id": 1, "name": "初中数学", "grade": "初中",
     "desc": "涵盖初一至初三数学核心知识点，含代数、几何、统计"}
)
db.commit()

# ── 2. agent_knowledge_points ─────────────────────────────
# 3-level tree: 章(level=1) → 节(level=2) → 知识点(level=3)
print("Inserting knowledge points...")

kps = [
    # Chapter 1: 有理数
    (1, 1, None, "有理数", 1, 1, 1.0),
    (2, 1, 1, "有理数的概念", 2, 2, 1.0),
    (3, 1, 2, "正负数的意义", 3, 3, 0.9),
    (4, 1, 2, "数轴与相反数", 3, 4, 0.9),
    (5, 1, 2, "绝对值", 3, 5, 1.0),
    (6, 1, 1, "有理数的运算", 2, 6, 1.2),
    (7, 1, 6, "加减法", 3, 7, 1.0),
    (8, 1, 6, "乘除法", 3, 8, 1.0),
    (9, 1, 6, "混合运算", 3, 9, 1.2),
    # Chapter 2: 整式与因式分解
    (10, 1, None, "整式与因式分解", 1, 10, 1.0),
    (11, 1, 10, "整式的加减", 2, 11, 1.0),
    (12, 1, 11, "同类项合并", 3, 12, 1.0),
    (13, 1, 11, "去括号与添括号", 3, 13, 0.9),
    (14, 1, 10, "因式分解", 2, 12, 1.2),
    (15, 1, 14, "提公因式法", 3, 13, 1.0),
    (16, 1, 14, "公式法", 3, 14, 1.0),
    (17, 1, 14, "十字相乘法", 3, 15, 1.2),
    # Chapter 3: 一次方程与不等式
    (18, 1, None, "一次方程与不等式", 1, 16, 1.0),
    (19, 1, 18, "一元一次方程", 2, 17, 1.0),
    (20, 1, 19, "方程解法", 3, 18, 1.0),
    (21, 1, 19, "列方程解应用题", 3, 19, 1.2),
    (22, 1, 18, "一元一次不等式", 2, 20, 1.0),
    (23, 1, 22, "不等式性质", 3, 21, 0.9),
    (24, 1, 22, "不等式组的解法", 3, 22, 1.0),
    # Chapter 4: 二次函数
    (25, 1, None, "二次函数", 1, 23, 1.2),
    (26, 1, 25, "二次函数的概念与图像", 2, 24, 1.2),
    (27, 1, 26, "图像与性质", 3, 25, 1.2),
    (28, 1, 26, "顶点式与交点式", 3, 26, 1.0),
    (29, 1, 25, "二次函数的应用", 2, 27, 1.2),
    (30, 1, 29, "最值问题", 3, 28, 1.3),
    (31, 1, 29, "二次函数与方程", 3, 29, 1.2),
    # Chapter 5: 几何基础
    (32, 1, None, "几何基础", 1, 30, 1.0),
    (33, 1, 32, "三角形", 2, 31, 1.0),
    (34, 1, 33, "三角形全等", 3, 32, 1.2),
    (35, 1, 33, "相似三角形", 3, 33, 1.2),
    (36, 1, 33, "勾股定理", 3, 34, 1.0),
    (37, 1, 32, "四边形", 2, 35, 1.0),
    (38, 1, 37, "平行四边形", 3, 36, 1.0),
    (39, 1, 37, "特殊四边形", 3, 37, 1.2),
    # Chapter 6: 统计与概率
    (40, 1, None, "统计与概率", 1, 38, 0.8),
    (41, 1, 40, "数据统计", 2, 39, 0.8),
    (42, 1, 41, "平均数与方差", 3, 40, 0.9),
    (43, 1, 41, "频数分布直方图", 3, 41, 0.8),
    (44, 1, 40, "概率初步", 2, 42, 0.8),
    (45, 1, 44, "简单概率计算", 3, 43, 0.8),
]

for kp in kps:
    db.execute(
        text("INSERT INTO agent_knowledge_points (id, subject_id, parent_id, name, level, sort_order, core_weight) "
             "VALUES (:id, :sid, :pid, :name, :lvl, :sort, :cw)"),
        {"id": kp[0], "sid": kp[1], "pid": kp[2], "name": kp[3],
         "lvl": kp[4], "sort": kp[5], "cw": kp[6]}
    )
db.commit()
print(f"  Inserted {len(kps)} knowledge points (6 chapters, 13 sections, 26 points)")

# ── 3. agent_knowledge_dependencies ──────────────────────
print("Inserting knowledge dependencies...")

deps = [
    (5, 7, 0.8),     # 绝对值 → 有理数加减法
    (7, 9, 0.9),     # 有理数加减 → 混合运算
    (8, 9, 0.9),     # 有理数乘除 → 混合运算
    (12, 13, 0.7),   # 同类项合并 → 去括号
    (15, 16, 0.8),   # 提公因式法 → 公式法
    (15, 17, 0.7),   # 提公因式法 → 十字相乘法
    (20, 21, 0.9),   # 方程解法 → 应用题
    (23, 24, 0.8),   # 不等式性质 → 不等式组
    (20, 31, 0.6),   # 方程解法 → 二次函数与方程的关系
    (27, 30, 0.8),   # 二次函数图像 → 最值问题
    (34, 35, 0.7),   # 三角形全等 → 相似三角形
    (36, 38, 0.5),   # 勾股定理 → 平行四边形
    (38, 39, 0.7),   # 平行四边形 → 特殊四边形
    (9, 12, 0.6),    # 有理数混合运算 → 整式加减
]

for dep in deps:
    db.execute(
        text("INSERT INTO agent_knowledge_dependencies (source_kp_id, target_kp_id, dependency_weight) "
             "VALUES (:src, :tgt, :w)"),
        {"src": dep[0], "tgt": dep[1], "w": dep[2]}
    )
db.commit()
print(f"  Inserted {len(deps)} dependency edges")

# ── 4. agent_exams ───────────────────────────────────────
print("Inserting exams...")

class_exams = [
    (1, 1, "初三(1)班第一次月考", date(2025, 3, 20), 120, "第一次月考", "2025下"),
    (2, 1, "初三(1)班第二次月考", date(2025, 4, 25), 120, "第二次月考", "2025下"),
    (3, 1, "初三(1)班期中考试", date(2025, 5, 10), 120, "期中考试", "2025下"),
    (4, 2, "初三(2)班第一次月考", date(2025, 3, 20), 120, "第一次月考", "2025下"),
    (5, 2, "初三(2)班第二次月考", date(2025, 4, 25), 120, "第二次月考", "2025下"),
    (6, 2, "初三(2)班期中考试", date(2025, 5, 10), 120, "期中考试", "2025下"),
    (7, 3, "初三(3)班第一次月考", date(2025, 3, 20), 120, "第一次月考", "2025下"),
    (8, 3, "初三(3)班第二次月考", date(2025, 4, 25), 120, "第二次月考", "2025下"),
    (9, 3, "初三(3)班期中考试", date(2025, 5, 10), 120, "期中考试", "2025下"),
]

for eid, cid, name, edate, total, etype, sem in class_exams:
    db.execute(
        text("INSERT INTO agent_exams (id, class_id, subject_id, name, exam_date, total_score, exam_type, semester) "
             "VALUES (:id, :cid, :sid, :name, :edate, :total, :etype, :sem)"),
        {"id": eid, "cid": cid, "sid": 1, "name": name, "edate": edate,
         "total": total, "etype": etype, "sem": sem}
    )
db.commit()
print(f"  Inserted {len(class_exams)} exams")

# ── 5. agent_questions ───────────────────────────────────
print("Inserting questions...")

q_template_per_exam = [
    ("有理数概念辨析", "选择题", 0.3, 1),
    ("有理数混合运算", "填空题", 0.4, 2),
    ("整式化简求值", "填空题", 0.4, 3),
    ("因式分解", "解答题", 0.5, 4),
    ("解一元一次方程", "解答题", 0.5, 5),
    ("列方程解应用题", "解答题", 0.6, 6),
    ("二次函数图像判断", "选择题", 0.5, 7),
    ("二次函数最值应用", "解答题", 0.7, 8),
    ("三角形全等证明", "证明题", 0.6, 9),
    ("平行四边形性质应用", "解答题", 0.6, 10),
    ("平均数与方差计算", "填空题", 0.3, 11),
    ("概率计算", "选择题", 0.4, 12),
]

qid = 0
for eid, _, _, _, _, _, _ in class_exams:
    for title, qtype, diff, order in q_template_per_exam:
        qid += 1
        db.execute(
            text("INSERT INTO agent_questions (id, exam_id, title, question_type, difficulty, max_score, sort_order) "
                 "VALUES (:id, :eid, :title, :qtype, :diff, :maxs, :sort)"),
            {"id": qid, "eid": eid, "title": title, "qtype": qtype,
             "diff": diff, "maxs": 10, "sort": order}
        )
db.commit()
print(f"  Inserted {qid} questions")

# ── 6. agent_question_kps ────────────────────────────────
print("Inserting question-knowledge-point mappings...")

q_kp_map = [
    [3, 4],     # Q1
    [7, 9],     # Q2
    [12, 13],   # Q3
    [15, 16],   # Q4
    [20],       # Q5
    [21],       # Q6
    [27],       # Q7
    [28, 30],   # Q8
    [34],       # Q9
    [38, 39],   # Q10
    [42],       # Q11
    [45],       # Q12
]

qkp_id = 0
for base_qid in range(0, qid, 12):
    for slot in range(12):
        actual_qid = base_qid + slot + 1
        for kp_id in q_kp_map[slot]:
            qkp_id += 1
            db.execute(
                text("INSERT INTO agent_question_kps (id, question_id, kp_id, relevance) "
                     "VALUES (:id, :qid, :kpid, :rel)"),
                {"id": qkp_id, "qid": actual_qid, "kpid": kp_id, "rel": 1.0}
            )
db.commit()
print(f"  Inserted {qkp_id} question-KP mappings")

# ── 7. agent_score_records ───────────────────────────────
print("Inserting score records...")

student_profiles = [
    # Class 1 (5 students): exams 1,2,3
    ("S2026001", 1, 68, 82, 75, [27, 28, 30, 34]),
    ("S2026002", 1, 95, 90, 93, [42, 45]),
    ("S2026004", 1, 75, 76, 80, [7, 9, 20, 21]),
    ("S2026007", 1, 90, 72, 85, [15, 16, 17, 27, 30]),
    ("S2026008", 1, 89, 75, 82, [12, 13, 15, 16]),
    # Class 2 (2 students): exams 4,5,6
    ("S2026003", 2, 78, 75, 82, [30, 31, 38, 39]),
    ("S2026010", 2, 68, 94, 78, [3, 4, 5, 7, 8, 9]),
    # Class 3 (3 students): exams 7,8,9
    ("S2026005", 3, 83, 78, 85, [34, 35, 36]),
    ("S2026006", 3, 91, 79, 88, [21, 23, 24]),
    ("S2026009", 3, 70, 87, 76, [28, 30, 31, 34, 35]),
]

score_id = 0
for student_no, class_id, target1, target2, target3, weak_kps in student_profiles:
    base_exam_id = (class_id - 1) * 3
    exam1_id = base_exam_id + 1
    exam2_id = base_exam_id + 2
    exam3_id = base_exam_id + 3

    for exam_id, target_total in [(exam1_id, target1), (exam2_id, target2), (exam3_id, target3)]:
        base_qid = (exam_id - 1) * 12
        scores = []
        for slot in range(12):
            qid = base_qid + slot + 1
            kps_for_q = q_kp_map[slot]
            is_weak_q = any(kp in weak_kps for kp in kps_for_q)
            if is_weak_q:
                s = random.uniform(2, 6)
            else:
                s = random.uniform(6, 10)
            scores.append((qid, round(s, 1)))

        current_sum = sum(s for _, s in scores)
        scale = target_total / current_sum if current_sum > 0 else 1.0
        for qid, s in scores:
            adjusted = round(s * scale, 1)
            adjusted = max(0, min(10, adjusted))
            score_id += 1
            db.execute(
                text("INSERT INTO agent_score_records (id, student_no, exam_id, question_id, score, max_score) "
                     "VALUES (:id, :sno, :eid, :qid, :score, :maxs)"),
                {"id": score_id, "sno": student_no, "eid": exam_id,
                 "qid": qid, "score": adjusted, "maxs": 10}
            )

db.commit()
print(f"  Inserted {score_id} score records")

# ── Summary ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("Mock data generation complete!")
print(f"  agent_subjects:              1 row")
print(f"  agent_knowledge_points:     {len(kps)} rows")
print(f"  agent_knowledge_dependencies: {len(deps)} rows")
print(f"  agent_exams:                {len(class_exams)} rows")
print(f"  agent_questions:            {qid} rows")
print(f"  agent_question_kps:         {qkp_id} rows")
print(f"  agent_score_records:        {score_id} rows")
print("=" * 60)

db.close()
