import logging
from sqlalchemy.orm import Session
from app.core.llm import chat
from app.repositories.xiyouji_journey_repository import XiyoujiJourneyRepository
from app.schemas.xiyouji import (
    JourneyResponse,
    KnowledgeCard,
    Achievement,
    ChoiceItem,
)

logger = logging.getLogger(__name__)

ACHIEVEMENT_DEFINITIONS = [
    {"id": "first_step", "name": "初踏取经路", "description": "完成第一章"},
    {"id": "monster_hunter", "name": "降妖初成", "description": "首次成功降服妖怪"},
    {"id": "scholar", "name": "西游学者", "description": "累计解锁5张知识卡片"},
    {"id": "wise_master", "name": "智者大师", "description": "连续3次选择正确"},
    {"id": "compassionate", "name": "慈悲为怀", "description": "功德值达到50"},
    {"id": "journey_complete", "name": "取经圆满", "description": "完成所有章节"},
]


def _unlock_achievement(journey, achievements: list[dict], achievement_id: str) -> list[dict]:
    for ach in achievements:
        if ach["id"] == achievement_id and not ach["unlocked"]:
            ach["unlocked"] = True
            return achievements
    return achievements


class XiyoujiJourneyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = XiyoujiJourneyRepository(db)

    def start_journey(self, session_id: str) -> JourneyResponse:
        journey = self.repo.create_journey(session_id)

        from app.config.xiyouji_chapters import get_first_chapter
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

        self.repo.advance_stage(
            session_id,
            stage="剧情选择",
            chapter=chapter["chapter"],
            stage_data=stage_data,
        )
        self.repo.update_progress(session_id, progress=5, karma=0)

        default_choices = [
            ChoiceItem(**c) for c in chapter["choices"]
        ]

        return JourneyResponse(
            think="",
            reply=f"阿弥陀佛。贫僧唐三藏，奉旨前往西天取经。施主既愿同行，此去十万八千里，山高路险，妖怪横行，不知施主可愿与贫僧同赴极乐，求得真经？\n\n施主当前位于第{chapter['chapter']}章：{chapter['name']}",
            scene_description=chapter["description"],
            stage="剧情选择",
            choices=default_choices,
            progress=5,
            karma=0,
            chapter=chapter["chapter"],
            level_id=journey.level_id,
            chapter_name=chapter["name"],
            monster_name=chapter["monster"]["name"],
            monster_description=chapter["monster"]["description"],
            knowledge_card=None,
            achievements=[],
            examples=None,
        )

    def handle_choice(self, session_id: str, choice: str) -> JourneyResponse:
        journey = self.repo.get_active_journey(session_id)
        if not journey:
            raise ValueError("无进行中的取经游戏")

        chapter_num = journey.chapter
        stage_data = journey.stage_data or {}

        from app.config.xiyouji_chapters import get_chapter, get_chapters_count
        chapter_cfg = get_chapter(chapter_num)

        choices = stage_data.get("choices", [])
        selected = None
        for c in choices:
            if c["text"] == choice or choice in c["text"]:
                selected = c
                break

        if not selected:
            selected = {"text": choice, "karma": 0, "success": False}

        karma_delta = selected.get("karma", 0)
        success = selected.get("success", False)
        new_karma = max(0, journey.karma + karma_delta)
        cleared = list(journey.cleared_chapters or [])

        achievements = list(journey.achievements or [])
        knowledge_card = None

        if success:
            cleared_ids = [c["id"] for c in ACHIEVEMENT_DEFINITIONS]

            if chapter_num == 1 and "first_step" not in [a["id"] for a in achievements if a["unlocked"]]:
                achievements = _unlock_achievement(journey, achievements, "first_step")

            if "monster_hunter" not in [a["id"] for a in achievements if a["unlocked"]]:
                if chapter_cfg["monster"]["name"] != "无":
                    achievements = _unlock_achievement(journey, achievements, "monster_hunter")

            if new_karma >= 50 and "compassionate" not in [a["id"] for a in achievements if a["unlocked"]]:
                achievements = _unlock_achievement(journey, achievements, "compassionate")

            if len(journey.knowledge_cards or []) >= 5 and "scholar" not in [a["id"] for a in achievements if a["unlocked"]]:
                achievements = _unlock_achievement(journey, achievements, "scholar")

            if chapter_cfg["knowledge"]:
                knowledge_card = KnowledgeCard(
                    title=chapter_cfg["knowledge"]["title"],
                    content=chapter_cfg["knowledge"]["content"],
                )
                current_cards = journey.knowledge_cards or []
                new_card = {"title": knowledge_card.title, "content": knowledge_card.content}
                if new_card not in current_cards:
                    current_cards.append(new_card)
                    self.repo.update_knowledge_cards(session_id, current_cards)

            if chapter_num not in cleared:
                cleared.append(chapter_num)
                self.repo.update_cleared_chapters(session_id, cleared)

            if chapter_num == get_chapters_count():
                achievements = _unlock_achievement(journey, achievements, "journey_complete")

            next_chapter_num = chapter_num + 1
            total = get_chapters_count()
            progress = int((chapter_num / total) * 100)

            if next_chapter_num > total:
                reply_text = "阿弥陀佛！施主与贫僧历经九九八十一难，终至灵山，取得真经。此番取经，施主功德无量，愿此行造福万民。阿弥陀佛！"
                scene_desc = "灵山雷音寺，真经在手，大功告成"
                next_chapter_name = "取得真经"
                monster_name = "无"
                monster_desc = "取经圆满"
                next_stage = "完成"
                next_choices = []
                level_id = journey.level_id
            else:
                next_chapter = get_chapter(next_chapter_num)
                reply_text = f"善哉善哉，施主此番选择颇有佛缘。\n\n施主获得知识卡片：{chapter_cfg['knowledge']['title']}\n\n让我们继续西行，进入第{next_chapter_num}章：{next_chapter['name']}"
                scene_desc = chapter_cfg["description"]
                next_chapter_name = next_chapter["name"]
                monster_name = next_chapter["monster"]["name"]
                monster_desc = next_chapter["monster"]["description"]
                next_stage = "剧情选择"
                next_choices = [ChoiceItem(**c) for c in next_chapter["choices"]]
                level_id = next_chapter_num

                next_stage_data = {
                    "chapter": next_chapter["chapter"],
                    "chapter_name": next_chapter["name"],
                    "description": next_chapter["description"],
                    "monster": next_chapter["monster"],
                    "knowledge": next_chapter["knowledge"],
                    "choices": next_chapter["choices"],
                    "choice_made": False,
                }
                self.repo.advance_stage(
                    session_id,
                    stage=next_stage,
                    chapter=next_chapter_num,
                    stage_data=next_stage_data,
                )
                self.repo.update_progress(session_id, progress, new_karma)
        else:
            reply_text = "阿弥陀佛！施主此番选择稍有不妥，需慎言慎行。取经之路考验心智，望施主三思而后行，再作抉择。"
            scene_desc = chapter_cfg["description"]
            next_chapter_name = chapter_cfg["name"]
            monster_name = chapter_cfg["monster"]["name"]
            monster_desc = chapter_cfg["monster"]["description"]
            next_stage = "剧情选择"
            next_choices = [ChoiceItem(**c) for c in chapter_cfg["choices"]]
            progress = journey.progress
            level_id = journey.level_id

        self.repo.update_achievements(session_id, achievements)

        return JourneyResponse(
            think="",
            reply=reply_text,
            scene_description=scene_desc,
            stage=next_stage,
            choices=next_choices,
            progress=progress,
            karma=new_karma,
            chapter=chapter_num if next_stage == "完成" else journey.chapter,
            level_id=level_id,
            chapter_name=next_chapter_name,
            monster_name=monster_name,
            monster_description=monster_desc,
            knowledge_card=knowledge_card,
            achievements=[Achievement(**a) for a in achievements],
            examples=None,
        )