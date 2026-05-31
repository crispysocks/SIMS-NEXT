from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
from app.core.config import API_PREFIX
from app.core.seed import seed_default_admin
from app.api.v1.student import router as student_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.class_router import router as class_router
from app.api.v1.score_router import router as score_router
from app.api.v1.auth import router as auth_router
from app.api.v1.novels import router as novels_router
from app.agent.api.v1.chat_router import router as agent_chat_router
from app.agent.api.v1.analysis_router import router as agent_analysis_router
from app.agent.api.v1.report_router import router as agent_report_router
from app.agent.api.v1.student_router import router as agent_student_router
from app.agent.api.v1.mock_router import router as agent_mock_router
from app.predict.api.v1.predict_router import router as predict_router
from app.predict.api.v1.admission_router import router as admission_router
from app.predict.api.v1.advice_router import router as advice_router
from app.api.v1.tutor_router import router as tutor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_default_admin()
    yield


app = FastAPI(title="SIMS-NEXT", description="Student Information Management System", lifespan=lifespan)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router, prefix=API_PREFIX)
app.include_router(teacher_router, prefix=API_PREFIX)
app.include_router(class_router, prefix=API_PREFIX)
app.include_router(score_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(predict_router, prefix=API_PREFIX)
app.include_router(admission_router, prefix=API_PREFIX)
app.include_router(advice_router, prefix=API_PREFIX)
app.include_router(novels_router, prefix=API_PREFIX)
app.include_router(tutor_router, prefix=API_PREFIX)

app.include_router(agent_chat_router, prefix=f"{API_PREFIX}/agent")
app.include_router(agent_analysis_router, prefix=f"{API_PREFIX}/agent")
app.include_router(agent_report_router, prefix=f"{API_PREFIX}/agent")
app.include_router(agent_student_router, prefix=f"{API_PREFIX}/agent")
app.include_router(agent_mock_router, prefix=f"{API_PREFIX}/agent")


@app.get("/health")
def health_check():
    return {"status": "ok"}