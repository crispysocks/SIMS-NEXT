from fastapi import FastAPI
from app.api.v1.student import router as student_router

app = FastAPI(title="SIMS-NEXT", description="Student Information Management System")

app.include_router(student_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}