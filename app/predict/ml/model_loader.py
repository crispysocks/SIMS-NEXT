import os
import pickle
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"


class ModelLoader:
    _instances = {}

    @classmethod
    def get_model(cls, model_name: str):
        if model_name in cls._instances:
            return cls._instances[model_name]

        model_path = MODEL_DIR / f"{model_name}.pkl"
        if not model_path.exists():
            return None

        with open(model_path, "rb") as f:
            model = pickle.load(f)
            cls._instances[model_name] = model
            return model

    @classmethod
    def save_model(cls, model_name: str, model):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODEL_DIR / f"{model_name}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)