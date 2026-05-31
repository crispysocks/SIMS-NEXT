from sqlalchemy.orm import Session

from app.core.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.xiyouji_journey import XiyoujiJourney
from app.services.auth_service import get_password_hash


def seed_default_admin() -> None:
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if existing:
            return

        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
            role="admin",
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


def create_missing_tables() -> None:
    Base.metadata.create_all(bind=engine)
