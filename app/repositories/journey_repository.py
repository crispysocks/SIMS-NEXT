from sqlalchemy.orm import Session
from typing import Optional
from app.models.journey import JourneyConversation, JourneyState


class JourneyRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_conversation_history(self, session_id: str, limit: int = 20) -> list[JourneyConversation]:
        return (
            self.db.query(JourneyConversation)
            .filter(JourneyConversation.session_id == session_id)
            .order_by(JourneyConversation.created_at.asc())
            .limit(limit)
            .all()
        )

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        personality: Optional[str] = None,
        emotion: Optional[str] = None,
        tone: Optional[str] = None,
    ) -> JourneyConversation:
        msg = JourneyConversation(
            session_id=session_id,
            role=role,
            content=content,
            personality=personality,
            emotion=emotion,
            tone=tone,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def create_journey(self, session_id: str, achievements: list[dict]) -> JourneyState:
        journey = JourneyState(
            session_id=session_id,
            companions=["Tang Monk", "Sun Wukong", "Zhu Bajie", "Sha Wujing"],
            achievements=achievements,
            knowledge_cards=[],
            cleared_chapters=[],
        )
        self.db.add(journey)
        self.db.commit()
        self.db.refresh(journey)
        return journey

    def get_active_journey(self, session_id: str) -> JourneyState | None:
        return (
            self.db.query(JourneyState)
            .filter(
                JourneyState.session_id == session_id,
                JourneyState.is_active == True,
            )
            .first()
        )

    def update_progress(self, session_id: str, progress: int, karma: int) -> JourneyState | None:
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
    ) -> JourneyState | None:
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

    def end_journey(self, session_id: str) -> JourneyState | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.is_active = False
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def update_knowledge_cards(self, session_id: str, cards: list) -> JourneyState | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.knowledge_cards = cards
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def update_achievements(self, session_id: str, achievements: list) -> JourneyState | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.achievements = achievements
            self.db.commit()
            self.db.refresh(journey)
        return journey

    def update_cleared_chapters(self, session_id: str, chapters: list) -> JourneyState | None:
        journey = self.get_active_journey(session_id)
        if journey:
            journey.cleared_chapters = chapters
            self.db.commit()
            self.db.refresh(journey)
        return journey
