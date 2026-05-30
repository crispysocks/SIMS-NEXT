"""Mock 数据 CLI 入口——python -m app.agent.mock 生成全套模拟数据。

使用方式:
  python -m app.agent.mock generate --classes 3 --students 90 --exams 6
  python -m app.agent.mock clean           # 清空所有 agent 表
  python -m app.agent.mock stats           # 查看数据统计
"""

import sys
import random
import argparse
from datetime import date

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.agent.mock.student_profile import generate_student_profiles
from app.agent.mock.knowledge_tree import (
    generate_knowledge_tree,
    generate_dependencies,
    generate_questions,
)
from app.agent.mock.score_generator import generate_scores, generate_exams

from app.agent.models.subject import Subject
from app.agent.models.knowledge_point import KnowledgePoint
from app.agent.models.knowledge_dependency import KnowledgeDependency
from app.agent.models.question import Question
from app.agent.models.question_kp import QuestionKnowledgePoint
from app.agent.models.exam import Exam
from app.agent.models.score_record import ScoreRecord
from app.models.student import Student


SEED = 42


def cmd_generate(args) -> None:
    """生成全套 Mock 数据并写入数据库。"""
    db: Session = SessionLocal()
    random.seed(SEED)

    try:
        _clean_all(db)

        print("=" * 60)
        print("开始生成 Mock 数据...")
        print(f"  班级数: {args.classes}, 每班学生: {args.students}")
        print(f"  每班考试数: {args.exams}, 随机种子: {SEED}")
        print("=" * 60)

        # 1. Subject
        subject = Subject(
            id=1, name="初中数学", grade_level="初中",
            description="九年级数学（人教版）"
        )
        db.add(subject)
        db.commit()
        print("[1/7] 学科创建: 初中数学")

        # 2. Knowledge Points
        kp_list = generate_knowledge_tree(subject_id=1)
        for kp in kp_list:
            db.add(KnowledgePoint(**kp))
        db.commit()
        print(f"[2/7] 知识点: {len(kp_list)} 个（三级树）")

        # 3. Dependencies
        dep_list = generate_dependencies(kp_list)
        for dep in dep_list:
            db.add(KnowledgeDependency(**dep))
        db.commit()
        print(f"[3/7] 依赖关系: {len(dep_list)} 条")

        # 4. Exams
        class_ids = list(range(1, args.classes + 1))
        exam_list = generate_exams(class_ids, exam_count=args.exams)
        for exam in exam_list:
            db.add(Exam(**exam))
        db.commit()
        print(f"[4/7] 考试: {len(exam_list)} 场 ({len(class_ids)} 个班 × {args.exams} 场)")

        # 5. Questions
        exam_ids = [e["id"] for e in exam_list]
        all_questions = generate_questions(exam_ids, kp_list, seed=SEED)
        for q in all_questions:
            kps_data = q.pop("kps")
            db.add(Question(**q))
            db.flush()
            for kp_ref in kps_data:
                db.add(QuestionKnowledgePoint(
                    question_id=q["id"],
                    kp_id=kp_ref["kp_id"],
                    relevance=kp_ref["relevance"],
                ))
        db.commit()
        print(f"[5/7] 题目: {len(all_questions)} 道 ({len(exam_ids)} 场 × {len(all_questions) // len(exam_ids)} 题/场)")

        # 6. Student Profiles
        all_profiles = []
        for cid in class_ids:
            profiles = generate_student_profiles(cid, args.students, seed=SEED)
            all_profiles.extend(profiles)
        student_count = len(all_profiles)
        first_student_name = all_profiles[0]["name"] if all_profiles else "N/A"
        print(f"[6/7] 学生画像: {student_count} 人 (示例: {first_student_name})")

        # 写入 students 表
        batch_size = 500
        student_records = [
            dict(
                student_no=p["student_no"],
                name=p["name"],
                gender=p["gender"],
                age=p["age"],
                class_id=p["class_id"],
                enrollment_date=p["enrollment_date"],
            )
            for p in all_profiles
        ]
        for i in range(0, len(student_records), batch_size):
            db.bulk_insert_mappings(Student, student_records[i:i + batch_size])
        db.commit()

        # 7. Score Records
        all_records = generate_scores(all_profiles, all_questions, kp_list, exam_list, seed=SEED)
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i + batch_size]
            db.bulk_insert_mappings(ScoreRecord, batch)
        db.commit()
        print(f"[7/7] 成绩记录: {len(all_records)} 条 (约 {len(all_records) // student_count} 条/人)")

        print("=" * 60)
        print("Mock 数据生成完成!")
        print_statistics(db)
        print("=" * 60)

    finally:
        db.close()


def cmd_clean(args) -> None:
    """清空所有 agent 表。"""
    db = SessionLocal()
    try:
        _clean_all(db)
        db.commit()
        print("已清空所有 agent 表。")
    finally:
        db.close()


def cmd_stats(args) -> None:
    """打印数据统计。"""
    db = SessionLocal()
    try:
        print_statistics(db)
    finally:
        db.close()


def _clean_all(db: Session) -> None:
    """按外键依赖顺序清空所有 agent 表（含 agent 运行时表）。

    使用 raw SQL + SET FOREIGN_KEY_CHECKS=0 避免自引用 FK
    (KnowledgePoint.parent_id → id) 和多表间 FK 的删除顺序问题。
    """
    from sqlalchemy import text

    tables = [
        "agent_score_records",
        "agent_question_kps",
        "agent_questions",
        "agent_knowledge_dependencies",
        "agent_knowledge_points",
        "agent_exams",
        "agent_subjects",
        "agent_sessions",
        "agent_messages",
        "agent_tool_calls",
        "agent_analysis_data",
        "students",
    ]
    db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for t in tables:
        db.execute(text(f"DELETE FROM {t}"))
    db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    db.commit()


def print_statistics(db: Session) -> None:
    print(f"  Subject: {db.query(Subject).count()}")
    print(f"  KnowledgePoint: {db.query(KnowledgePoint).count()}")
    print(f"  KnowledgeDependency: {db.query(KnowledgeDependency).count()}")
    print(f"  Exam: {db.query(Exam).count()}")
    print(f"  Question: {db.query(Question).count()}")
    print(f"  QuestionKP: {db.query(QuestionKnowledgePoint).count()}")
    print(f"  ScoreRecord: {db.query(ScoreRecord).count()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Mock 数据管理")
    subparsers = parser.add_subparsers(dest="command")

    gen = subparsers.add_parser("generate", help="生成全套 Mock 数据")
    gen.add_argument("--classes", type=int, default=3, help="班级数量 (默认: 3)")
    gen.add_argument("--students", type=int, default=5, help="每班学生数 (默认: 5)")
    gen.add_argument("--exams", type=int, default=6, help="每班考试数 (默认: 6)")

    subparsers.add_parser("clean", help="清空所有 agent 表")
    subparsers.add_parser("stats", help="查看数据统计")

    args = parser.parse_args()
    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
