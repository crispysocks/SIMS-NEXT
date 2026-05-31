"""
Journey to the West game state machine.
"""

import logging
from sqlalchemy.orm import Session
from app.repositories.journey_repository import JourneyRepository
from app.config.journey_chapters import get_chapter, get_first_chapter, get_chapters_count

logger = logging.getLogger(__name__)

ACHIEVEMENTS = [
    {"id": "first_step", "name": "初踏取经路", "description": "完成第一章"},
    {"id": "monster_hunter", "name": "降妖初成", "description": "首次成功降服妖怪"},
    {"id": "scholar", "name": "西游学者", "description": "累计解锁5张知识卡片"},
    {"id": "wise_master", "name": "智者大师", "description": "连续3次选择正确"},
    {"id": "compassionate", "name": "慈悲为怀", "description": "功德值达到50"},
    {"id": "journey_complete", "name": "取经圆满", "description": "完成所有章节"},
]


class JourneyEngine:
    """Game state machine for Journey to the West adventure."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = JourneyRepository(db)

    def start(self, session_id: str) -> dict:
        """Start a new journey, returning the initial chapter state."""
        achievements_init = [{**a, "unlocked": False} for a in ACHIEVEMENTS]
        journey = self.repo.create_journey(session_id, achievements_init)
        chapter = get_first_chapter()
        stage_data = {
            "chapter": chapter["chapter"],
            "chapter_name": chapter["name"],
            "description": chapter["description"],
            "monster": chapter["monster"],
            "knowledge": chapter["knowledge"],
            "choices": chapter["choices"],
            "choice_made": False,
        }
        self.repo.advance_stage(session_id, stage="choice", chapter=chapter["chapter"], stage_data=stage_data)
        self.repo.update_progress(session_id, progress=5, karma=0)
        return {
            "reply": (
                f"Amitabha. I am Tripitaka, sworn to journey west for the sacred scriptures. "
                f"Together we shall face the perils ahead. "
                f"Chapter {chapter['chapter']}: {chapter['name']}"
            ),
            "scene_description": chapter["description"],
            "stage": "choice",
            "choices": chapter["choices"],
            "progress": 5,
            "karma": 0,
            "chapter": chapter["chapter"],
            "level_id": journey.level_id,
            "chapter_name": chapter["name"],
            "monster_name": chapter["monster"]["name"],
            "monster_description": chapter["monster"]["description"],
            "knowledge_card": None,
            "achievements": achievements_init,
        }

    def choose(self, session_id: str, choice_text: str) -> dict:
        """Process a player's choice in the current chapter."""
        journey = self.repo.get_active_journey(session_id)
        if not journey:
            raise ValueError("No active journey")

        chapter_num = journey.chapter
        chapter_cfg = get_chapter(chapter_num)
        stage_data = journey.stage_data or {}
        choices = stage_data.get("choices", [])

        selected = next((c for c in choices if c["text"] == choice_text or choice_text in c["text"]), None)
        if not selected:
            selected = {"text": choice_text, "karma": 0, "success": False}

        success = selected.get("success", False)
        karma_delta = selected.get("karma", 0)
        new_karma = max(0, journey.karma + karma_delta)
        achievements = list(journey.achievements or [])
        knowledge_card = None
        cleared = list(journey.cleared_chapters or [])

        if success:
            achievements = self._evaluate_achievements(journey, chapter_cfg, chapter_num, new_karma, achievements)
            knowledge_card = self._collect_knowledge_card(journey, chapter_cfg, session_id)
            if chapter_num not in cleared:
                cleared.append(chapter_num)
                self.repo.update_cleared_chapters(session_id, cleared)

            total = get_chapters_count()
            progress = int((chapter_num / total) * 100)

            if chapter_num >= total:
                return self._build_completion(journey, new_karma, achievements)

            next_chapter = get_chapter(chapter_num + 1)
            next_stage_data = {
                "chapter": next_chapter["chapter"],
                "chapter_name": next_chapter["name"],
                "description": next_chapter["description"],
                "monster": next_chapter["monster"],
                "knowledge": next_chapter["knowledge"],
                "choices": next_chapter["choices"],
                "choice_made": False,
            }
            self.repo.advance_stage(session_id, stage="choice", chapter=chapter_num + 1, stage_data=next_stage_data)
            self.repo.update_progress(session_id, progress, new_karma)
            self.repo.update_achievements(session_id, achievements)

            return {
                "reply": f"Well done! Chapter {chapter_num} cleared.\n\nChapter {chapter_num + 1}: {next_chapter['name']}",
                "scene_description": next_chapter["description"],
                "stage": "choice",
                "choices": next_chapter["choices"],
                "progress": progress,
                "karma": new_karma,
                "chapter": chapter_num + 1,
                "level_id": next_chapter["chapter"],
                "chapter_name": next_chapter["name"],
                "monster_name": next_chapter["monster"]["name"],
                "monster_description": next_chapter["monster"]["description"],
                "knowledge_card": knowledge_card,
                "achievements": achievements,
            }
        else:
            self.repo.update_progress(session_id, journey.progress, new_karma)
            self.repo.update_achievements(session_id, achievements)
            return {
                "reply": "Amitabha. That choice was not the wisest. Consider carefully and try again.",
                "scene_description": chapter_cfg["description"],
                "stage": "choice",
                "choices": chapter_cfg["choices"],
                "progress": journey.progress,
                "karma": new_karma,
                "chapter": chapter_num,
                "level_id": journey.level_id,
                "chapter_name": chapter_cfg["name"],
                "monster_name": chapter_cfg["monster"]["name"],
                "monster_description": chapter_cfg["monster"]["description"],
                "knowledge_card": None,
                "achievements": achievements,
            }

    def get_status(self, session_id: str) -> dict:
        """Get the current journey status."""
        journey = self.repo.get_active_journey(session_id)
        if not journey:
            return {"status": "not_started"}
        return {
            "status": "active",
            "user_role": journey.user_role,
            "current_stage": journey.current_stage or "unknown",
            "progress": journey.progress,
            "karma": journey.karma,
            "companions": journey.companions or [],
            "chapter": journey.chapter,
            "level_id": journey.level_id,
            "knowledge_cards": journey.knowledge_cards or [],
            "achievements": journey.achievements or [],
            "cleared_chapters": journey.cleared_chapters or [],
        }

    def _evaluate_achievements(self, journey, chapter_cfg, chapter_num, new_karma, achievements):
        """Evaluate and unlock achievements based on game state."""
        def _unlock(ach_id):
            for a in achievements:
                if a["id"] == ach_id and not a.get("unlocked"):
                    a["unlocked"] = True
            return achievements

        if chapter_num == 1:
            achievements = _unlock("first_step")
        monster_name = chapter_cfg["monster"]["name"]
        if monster_name and monster_name != "无" and monster_name != "None":
            achievements = _unlock("monster_hunter")
        if new_karma >= 50:
            achievements = _unlock("compassionate")
        if len(journey.knowledge_cards or []) >= 5:
            achievements = _unlock("scholar")
        if chapter_num >= get_chapters_count():
            achievements = _unlock("journey_complete")
        return achievements

    def _collect_knowledge_card(self, journey, chapter_cfg, session_id):
        """Collect the knowledge card for the current chapter."""
        knowledge = chapter_cfg.get("knowledge")
        if not knowledge:
            return None
        card = {"title": knowledge["title"], "content": knowledge["content"]}
        current_cards = list(journey.knowledge_cards or [])
        if card not in current_cards:
            current_cards.append(card)
            self.repo.update_knowledge_cards(session_id, current_cards)
        return card

    def _build_completion(self, journey, new_karma, achievements):
        """Build the completion response when all chapters are cleared."""
        return {
            "reply": "Amitabha! After all trials, we have reached the Thunderclap Monastery and obtained the true scriptures. The journey is complete!",
            "scene_description": "Thunderclap Monastery -- the sacred scriptures are in hand.",
            "stage": "completed",
            "choices": [],
            "progress": 100,
            "karma": new_karma,
            "chapter": journey.chapter,
            "level_id": journey.level_id,
            "chapter_name": "Journey's End",
            "monster_name": "None",
            "monster_description": "Journey complete",
            "knowledge_card": None,
            "achievements": achievements,
        }
