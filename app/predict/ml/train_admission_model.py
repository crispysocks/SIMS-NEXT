"""
录取概率模型训练脚本 (XGBoost)
用法: python -m app.predict.ml.train_admission_model
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.predict.repositories.admission_line_repository import AdmissionLineRepository
from app.predict.repositories.high_school_repository import HighSchoolRepository
from app.predict.ml.model_loader import ModelLoader


def prepare_training_data(db: Session) -> pd.DataFrame:
    """
    准备训练数据
    Note: 真实实现需要标注数据（学生分数 + 实际录取结果）
    当前为placeholder实现
    """
    repo = AdmissionLineRepository(db)
    school_repo = HighSchoolRepository(db)
    schools = school_repo.get_all()

    data = []
    for school in schools:
        lines = repo.get_by_school(school.id, limit_years=5)
        if len(lines) < 2:
            continue

        # Extract features from historical data
        scores = [float(line.admission_score) for line in lines]
        features = {
            "school_id": school.id,
            "mean_score": np.mean(scores),
            "std_score": np.std(scores) if len(scores) > 1 else 0,
            "trend": scores[-1] - scores[0],
            "latest_score": scores[0],
            "school_level": {"L1": 0.2, "L2": 0.5, "L3": 0.8, "L4": 1.0}.get(school.school_level, 0.5),
        }
        data.append(features)

    return pd.DataFrame(data)


def train_admission_model():
    db = SessionLocal()
    try:
        df = prepare_training_data(db)
        if df.empty:
            print("Not enough data for admission model training")
            print("Please ensure high schools and admission lines data exists")
            return

        # Placeholder: using sklearn instead of XGBoost
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
        model.fit(df.drop("school_id", axis=1), df["school_level"])

        ModelLoader.save_model("admission_prediction", model)
        print("Admission prediction model trained and saved")

    finally:
        db.close()


if __name__ == "__main__":
    train_admission_model()