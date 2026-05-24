from fastapi import FastAPI
from app.api.v1.student import router as student_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.class_router import router as class_router
from app.api.v1.score_router import router as score_router

app = FastAPI(title="SIMS-NEXT", description="Student Information Management System")

app.include_router(student_router, prefix="/api/v1")
app.include_router(teacher_router, prefix="/api/v1")
app.include_router(class_router, prefix="/api/v1")
app.include_router(score_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}