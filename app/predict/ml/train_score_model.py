"""
分数预测模型训练脚本 (LightGBM)
用法: python -m app.predict.ml.train_score_model
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.predict.repositories.exam_record_repository import ExamRecordRepository
from app.predict.ml.model_loader import ModelLoader


def extract_features(records: list) -> pd.DataFrame:
    """从考试记录中提取特征"""
    if not records:
        return pd.DataFrame()

    data = []
    # Group by student_id
    from itertools import groupby
    records_sorted = sorted(records, key=lambda x: x.student_id)
    for student_id, group in groupby(records_sorted, key=lambda x: x.student_id):
        group_list = list(group)
        scores = [float(r.score) for r in group_list]

        if len(scores) < 2:
            continue

        features = {
            "student_id": student_id,
            "mean_score": np.mean(scores),
            "std_score": np.std(scores) if len(scores) > 1 else 0,
            "max_score": max(scores),
            "min_score": min(scores),
            "trend": scores[-1] - scores[0],
            "latest_score": scores[0],
        }
        data.append(features)

    return pd.DataFrame(data)


def train_score_model():
    db = SessionLocal()
    try:
        repo = ExamRecordRepository(db)
        # Get all exam records
        from app.predict.models.exam_record import ExamRecord
        records = db.query(ExamRecord).filter(ExamRecord.is_deleted == False).all()

        if not records:
            print("No exam records found for training")
            return

        df = extract_features(records)
        if df.empty:
            print("Not enough data for training")
            return

        # Target: predict next exam score (using mean_score as proxy)
        X = df.drop(["student_id", "latest_score"], axis=1)
        y = df["latest_score"]

        # Using simple model for now (LightGBM requires additional installation)
        # Placeholder: using sklearn instead
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X, y)

        ModelLoader.save_model("score_prediction", model)
        print("Score prediction model trained and saved")

    finally:
        db.close()


if __name__ == "__main__":
    train_score_model()