from fastapi import FastAPI
from app.api.v1.teacher import router as teacher_router

app = FastAPI(title="SIMS-NEXT", description="Student Information Management System")

app.include_router(teacher_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}