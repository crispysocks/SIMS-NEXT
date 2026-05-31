from sqlalchemy.orm import Session
from app.models.xiyouji_journey import XiyoujiJourney


class XiyoujiJourneyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_journey(self, session_id: str) -> XiyoujiJourney:
        from app.services.xiyouji_journey_service import ACHIEVEMENT_DEFINITIONS
        journey = XiyoujiJourney(
            session_id=session_id,
            companions=["唐僧", "孙悟空", "猪八戒", "沙僧"],
            achievements=[{"id": a["id"], "name": a["name"], "description": a["description"], "unlocked": False} for a in ACHIEVEMENT_DEFINITIONS],
            knowledge_cards=[],
            cleared_chapters=[],
        )
        self.db.add(journey)
        self.db.commit()
        self.db.refresh(journey)
        return journey

    def get_active_journey(self, session_id: str) -> XiyoujiJourney | None:
        return (
            self.db.query(XiyoujiJourney)
            .filter(
                XiyoujiJourney.session_id == session_id,
                XiyoujiJourney.is_active == True,
            )
            .first()
        )

    def update_progress(
        self, session_id: str, progress: int, karma: int
    ) -> XiyoujiJourney | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.progress = progress
            journey.karma = karma
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def advance_stage(
        self,
        session_id: str,
        stage: str,
        chapter: int | None = None,
        stage_data: dict | None = None,
    ) -> XiyoujiJourney | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.current_stage = stage
            if chapter is not None:
                journey.chapter = chapter
            if stage_data is not None:
                journey.stage_data = stage_data
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def end_journey(self, session_id: str) -> XiyoujiJourney | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.is_active = False
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def update_knowledge_cards(self, session_id: str, cards: list) -> XiyoujiJourney | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.knowledge_cards = cards
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def update_achievements(self, session_id: str, achievements: list) -> XiyoujiJourney | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.achievements = achievements
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def update_cleared_chapters(self, session_id: str, chapters: list) -> XiyoujiJourney | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.cleared_chapters = chapters
            self.db.commit()
            self.db.refresh(journey)
        return journey