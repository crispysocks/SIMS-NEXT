from fastapi import FastAPI
from app.core.config import API_PREFIX
from app.api.v1.student import router as student_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.class_router import router as class_router
from app.api.v1.score_router import router as score_router
from app.api.v1.auth import router as auth_router

app = FastAPI(title="SIMS-NEXT", description="Student Information Management System")

app.include_router(student_router, prefix=API_PREFIX)
app.include_router(teacher_router, prefix=API_PREFIX)
app.include_router(class_router, prefix=API_PREFIX)
app.include_router(score_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)

@app.get("/health")
def health_check():
    return {"status": "ok"}