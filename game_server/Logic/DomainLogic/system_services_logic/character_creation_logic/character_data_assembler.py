# game_server\Logic\DomainLogic\system_services_logic\character_creation_logic\character_data_assembler.py

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Callable, List

import inject
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты
from game_server.config.constants import game_rules
from game_server.database.models.models import Character, CharacterSpecial, CharacterSkills
from game_server.config.logging.logging_setup import app_logger as logger

# TODO: Импортировать репозитории, когда они понадобятся для извлечения доп. данных
# from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import IReputationRepository

class CharacterDataAssembler:
    """
    Собирает единый, вложенный документ персонажа для MongoDB из ORM-модели Character
    и связанных с ней данных, согласно новой архитектуре.
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    def _assemble_core_data(self, character: Character, creature_type_name: str) -> Dict[str, Any]:
        """Собирает вложенный объект 'core'."""
        core_data = {
            "name": character.name,
            "surname": character.surname,
            "gender": character.gender,
            "creature_type": {"id": character.creature_type_id, "name": creature_type_name},
            "personality": character.personality.to_dict() if character.personality else None,
            "background_story": character.background_story.to_dict() if character.background_story else None,
        }
        self._logger.debug(f"[Assembler] Собран блок 'core': {core_data}")
        return core_data

    def _assemble_skills_data(self, character_skills: List[CharacterSkills]) -> List[Dict[str, Any]]:
        """Собирает список навыков."""
        skills_data = [
            {
                "skill_key": cs.skill_key,
                "name": cs.skills.name,
                "level": cs.level,
                "xp": cs.xp,
                "progress_state": cs.progress_state
            }
            for cs in character_skills
        ]
        self._logger.debug(f"[Assembler] Собран блок 'skills' из {len(skills_data)} навыков.")
        return skills_data
        
    async def assemble_warm_cache_document(
        self,
        character: Character,
        creature_type_name: str,
        # TODO: В будущем сюда можно передавать сессию для дозагрузки данных
        # session: AsyncSession 
    ) -> Dict[str, Any]:
        """
        Собирает и возвращает вложенный словарь для MongoDB.
        """
        self._logger.info(f"Сборка документа (новая структура) для персонажа ID {character.character_id}")

        # --- Собираем все части документа ---

        base_stats_obj = character.special_stats
        # Исключаем служебные поля SQLAlchemy из словаря
        base_stats_dict = {c.name: getattr(base_stats_obj, c.name) for c in CharacterSpecial.__table__.columns if c.name != 'character_id'} if base_stats_obj else {}
        self._logger.debug(f"[Assembler] Собран блок 'stats.base': {base_stats_dict}")

        # TODO: Реализовать логику расчета производных статов. Пока заглушка.
        derived_stats_dict = {item['stat_name']: item['value'] for item in game_rules.INITIAL_DERIVED_STATS}
        self._logger.debug(f"[Assembler] Собран блок 'derived_stats' из {len(derived_stats_dict)} параметров.")
        
        # TODO: Реализовать получение репутации. Пока заглушка.
        # reputation_repo = self._reputation_repo_factory(session)
        # reputation_data = await reputation_repo.get_for_character(character.character_id)
        reputation_dict = {"placeholder": "not_implemented"}
        self._logger.debug(f"[Assembler] Собран блок 'reputation': {reputation_dict}")

        # --- Собираем итоговый документ ---
        doc = {
            "_id": character.character_id,
            "account_id": character.account_id,
            "clan_id": character.clan_id,

            "core": self._assemble_core_data(character, creature_type_name),
            
            "location": {
                "current": {
                    "location_id": game_rules.INITIAL_LOCATION["current_location_id"],
                    "region_id": game_rules.INITIAL_LOCATION["current_region_id"],
                },
                "previous": {
                    "location_id": None,
                    "region_id": None,
                }
            },
            "vitals": {
                "current_hp": game_rules.INITIAL_VITALS['hp'],
                "max_hp": game_rules.INITIAL_VITALS['hp'],
                "current_mana": game_rules.INITIAL_VITALS['mana'],
                "max_mana": game_rules.INITIAL_VITALS['mana'],
            },
            "stats": {"base": base_stats_dict},
            "derived_stats": derived_stats_dict,
            "abilities": [],
            "items": {"equipped": [], "in_bags": []},
            "skills": self._assemble_skills_data(character.character_skills),
            "quests": {"active": [], "completed": []},
            "reputation": reputation_dict,
            "session": {
                "status": "online",
                "last_login_at": datetime.now(timezone.utc).isoformat(),
                "last_logout_at": None,
                "total_playtime_seconds": 0,
            }
        }
        self._logger.info(f"Документ для персонажа ID {character.character_id} собран успешно.")
        self._logger.debug(f"Итоговый документ: {doc}")
        return doc
