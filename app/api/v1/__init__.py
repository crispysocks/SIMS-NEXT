from app.api.v1.teacher import router as teacher_router
from app.api.v1.auth import router as auth_router

__all__ = ["teacher_router", "auth_router"]