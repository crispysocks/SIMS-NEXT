from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "sims")

<<<<<<< HEAD
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# MiniMax API
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
=======
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
>>>>>>> origin/main
