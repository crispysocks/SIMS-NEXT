<<<<<<< HEAD
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
=======
from fastapi import FastAPI
>>>>>>> origin/main
from app.api.v1.student import router as student_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.class_router import router as class_router
from app.api.v1.score_router import router as score_router
<<<<<<< HEAD
from app.predict.api.v1.predict_router import router as predict_router
from app.predict.api.v1.admission_router import router as admission_router
from app.predict.api.v1.advice_router import router as advice_router

app = FastAPI(title="SIMS-NEXT", description="Student Information Management System")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
=======

app = FastAPI(title="SIMS-NEXT", description="Student Information Management System")

>>>>>>> origin/main
app.include_router(student_router, prefix="/api/v1")
app.include_router(teacher_router, prefix="/api/v1")
app.include_router(class_router, prefix="/api/v1")
app.include_router(score_router, prefix="/api/v1")
<<<<<<< HEAD
app.include_router(predict_router, prefix="/api/v1")
app.include_router(admission_router, prefix="/api/v1")
app.include_router(advice_router, prefix="/api/v1")

# 预测模块静态文件目录
PREDICT_STATIC_DIR = Path(__file__).parent / "predict" / "static"

# 挂载静态文件目录 - /static 路径
import os
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predict", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def index():
    """首页"""
    return HTMLResponse("""
    <html>
    <head><title>SIMS-NEXT</title></head>
    <body>
        <h1>SIMS-NEXT 学生信息管理系统</h1>
        <ul>
            <li><a href="/predict/chat.html">升学预测AI分析</a></li>
            <li><a href="/docs">API文档</a></li>
        </ul>
    </body>
    </html>
    """)


@app.get("/predict")
def predict_index():
    """预测模块首页"""
    return HTMLResponse("""
    <html>
    <head><title>升学预测</title><meta http-equiv="refresh" content="0;url=/predict/chat.html"></head>
    <body>
        <p>正在跳转到 <a href="/predict/chat.html">升学预测AI分析</a>...</p>
    </body>
    </html>
    """)
=======

@app.get("/health")
def health_check():
    return {"status": "ok"}
>>>>>>> origin/main
