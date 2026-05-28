"""
升学预测模块 Mock数据生成脚本
用法: python scripts/generate_mock_data.py [--count 20] [--student-count 50]
"""
import sys
import argparse
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.predict.models.high_school import HighSchool
from app.predict.models.admission_line import AdmissionScoreLine
from app.predict.models.exam_record import ExamRecord
from app.predict.models.score_rank_line import ScoreRankLine

TIER_NAMES = {
    "L1": "职业教育",
    "L2": "普通高中",
    "L3": "重点高中",
    "L4": "顶级高中"
}

REGIONS = ["市区", "郊区", "县城", "乡镇"]

AREAS = ["城区", "开发区", "老城区"]  # 一分一段表地区

SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "政治"]

EXAM_NAMES = [
    "七年级上学期期中考试",
    "七年级上学期期末考试",
    "七年级下学期期中考试",
    "七年级下学期期末考试",
    "八年级上学期期中考试",
    "八年级上学期期末考试",
    "八年级下学期期中考试",
    "八年级下学期期末考试",
    "九年级上学期期中考试",
    "九年级上学期期末考试",
    "九年级一模考试",
    "九年级二模考试",
]


def generate_high_schools(db: Session, count: int = 20) -> list:
    schools = []
    levels = ["L1", "L2", "L2", "L3", "L3", "L3", "L4", "L4"]

    school_names = [
        "第一职业教育中心", "第二职业教育中心",
        "第一中学", "第二中学", "第三中学", "第四中学", "第五中学",
        "实验中学", "外国语学校", "师范附属中学",
        "第一重点高中", "第二重点高中", "省实验中学", "市重点中学",
        "顶级中学", "状元中学", "精英中学", "启航中学", "卓越中学"
    ]

    for i in range(min(count, len(school_names))):
        school = HighSchool(
            school_name=school_names[i],
            school_level=levels[i % len(levels)],
            region=random.choice(REGIONS),
            annual_admission_count=random.randint(200, 800)
        )
        db.add(school)
        schools.append(school)

    db.commit()
    print(f"Generated {len(schools)} high schools")
    return schools


def generate_admission_lines(db: Session, schools: list, years: int = 5):
    lines = []
    # 录取排名范围：L1最易进（高排名），L4最难（低排名）
    rank_ranges = {
        "L1": (20000, 45000),  # 职业教育：录取排名20000-45000
        "L2": (8000, 20000),   # 普通高中：录取排名8000-20000
        "L3": (3000, 8000),    # 重点高中：录取排名3000-8000
        "L4": (500, 3000),     # 顶级高中：录取排名500-3000
    }
    # 分数线范围（根据排名反推：排名越高，分数线越低）
    score_ranges = {
        "L1": (350, 450),      # 职业教育：350-450分
        "L2": (450, 550),      # 普通高中：450-550分
        "L3": (550, 650),      # 重点高中：550-650分
        "L4": (650, 750),      # 顶级高中：650-750分
    }

    for school in schools:
        for year_offset in range(years):
            year = 2026 - years + year_offset + 1
            rank_range = rank_ranges.get(school.school_level, (5000, 15000))
            score_range = score_ranges.get(school.school_level, (450, 550))
            admission_rank = random.randint(rank_range[0], rank_range[1])
            # 分数线根据排名反比例计算：rank越高，分数线越低
            rank_mid = (rank_range[0] + rank_range[1]) / 2
            score_mid = (score_range[0] + score_range[1]) / 2
            # 排名在范围内越低，分数线越高
            score = score_mid + (rank_mid - admission_rank) / rank_mid * 50
            score = max(score_range[0], min(score_range[1], score))
            lines.append(AdmissionScoreLine(
                school_id=school.id,
                year=year,
                admission_score=score,
                admission_rank=admission_rank,
                student_count=school.annual_admission_count
            ))

    for line in lines:
        db.add(line)
    db.commit()
    print(f"Generated {len(lines)} admission score lines")


def generate_exam_records(db: Session, student_ids: list, exams_per_student: int = 10) -> int:
    records = []
    for student_id in student_ids[:50]:  # Limit to 50 students
        for i in range(exams_per_student):
            exam_name = EXAM_NAMES[i % len(EXAM_NAMES)]
            exam_time = datetime.now() - timedelta(days=(exams_per_student - i) * 90)

            for subject in SUBJECTS:  # 6 core subjects
                base_score = random.randint(60, 95)
                score = base_score + random.randint(-5, 10)
                records.append(ExamRecord(
                    student_id=student_id,
                    student_no=f"S{student_id:06d}",
                    exam_name=exam_name,
                    subject=subject,
                    score=score,
                    ranking=random.randint(1, 100),
                    exam_time=exam_time
                ))

    for record in records:
        db.add(record)
    db.commit()
    print(f"Generated {len(records)} exam records")
    return len(records)


def generate_score_rank_lines(db: Session, years: int = 3):
    """生成一分一段表数据"""
    lines = []
    total_students = 50000  # 假设区域总考生人数

    for year in [2024, 2025, 2026]:
        for area in AREAS:
            rank_counter = 1
            # 从750分往下生成，每5分一段
            for score in range(750, 299, -5):
                # 本段人数：高分少，低分多（正态分布近似）
                if score > 650:
                    segment_count = random.randint(50, 200)
                elif score > 550:
                    segment_count = random.randint(200, 800)
                elif score > 450:
                    segment_count = random.randint(800, 2000)
                elif score > 350:
                    segment_count = random.randint(2000, 5000)
                else:
                    segment_count = random.randint(3000, 8000)

                rank_min = rank_counter
                rank_max = rank_counter + segment_count - 1
                rank_counter += segment_count

                # 限制不超过总人数
                if rank_max > total_students:
                    rank_max = total_students

                lines.append(ScoreRankLine(
                    year=year,
                    region=area,
                    score_min=score - 4,
                    score_max=score,
                    rank_min=rank_min,
                    rank_max=rank_max
                ))

    for line in lines:
        db.add(line)
    db.commit()
    print(f"Generated {len(lines)} score rank lines (一分一段表)")
    return len(lines)


def main():
    parser = argparse.ArgumentParser(description="生成升学预测模块Mock数据")
    parser.add_argument("--count", type=int, default=20, help="高中学校数量")
    parser.add_argument("--student-count", type=int, default=50, help="生成成绩的学生数量")
    args = parser.parse_args()

    # Import models to ensure they're registered
    from app.predict.models import high_school, admission_line, exam_record, score_rank_line
    from app.models.student import Student

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(HighSchool).first()
        if existing:
            print("Mock data already exists, skipping...")
            return

        schools = generate_high_schools(db, args.count)
        generate_admission_lines(db, schools, years=5)

        # 生成一分一段表
        generate_score_rank_lines(db, years=3)

        # Get some student IDs for exam records
        students = db.query(Student).limit(args.student_count).all()
        for s in students:
            s.region = random.choice(AREAS)
        db.commit()

        student_ids = [s.id for s in students]
        if student_ids:
            generate_exam_records(db, student_ids, exams_per_student=10)
        else:
            print("No students found in database, skipping exam records generation")

        print("Mock data generation completed!")

    finally:
        db.close()


if __name__ == "__main__":
    main()