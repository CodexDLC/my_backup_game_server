# game_server/Logic/InfrastructureLogic/app_post/repository_groups/character/character_skill_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, insert # Добавлен insert

from game_server.database.models.models import CharacterSkills, Skills
from .interfaces_character import ICharacterSkillRepository
from game_server.config.logging.logging_setup import app_logger as logger


class CharacterSkillRepositoryImpl(ICharacterSkillRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью CharacterSkills.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """

    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_skill(self, character_id: int, skill_data: Dict[str, Any]) -> CharacterSkills:
        """
        Добавление нового навыка персонажу в рамках переданной сессии.
        :param character_id: ID персонажа.
        :param skill_data: Словарь с данными для нового навыка.
        :return: Созданный объект CharacterSkills.
        """
        new_skill = CharacterSkills(character_id=character_id, **skill_data)
        self.db_session.add(new_skill)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Навык '{skill_data.get('skill_key', 'N/A')}' добавлен персонажу {character_id} в сессию.")
        return new_skill

    async def get_skill(self, character_id: int, skill_key: int) -> Optional[CharacterSkills]:
        """
        Получение навыка персонажа в рамках переданной сессии.
        """
        stmt = select(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_skill(self, character_id: int, skill_key: int, updates: Dict[str, Any]) -> Optional[CharacterSkills]:
        """
        Обновление навыка персонажа в рамках переданной сессии.
        """
        stmt = update(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        ).values(**updates).returning(CharacterSkills)
        result = await self.db_session.execute(stmt)
        updated_skill = result.scalars().first()
        if updated_skill:
            await self.db_session.flush() # flush, но НЕ commit
            logger.info(f"Навык `{skill_key}` у персонажа `{character_id}` обновлён в сессии.")
        else:
            logger.warning(f"Навык `{skill_key}` у персонажа `{character_id}` не найден для обновления.")
        return updated_skill

    async def delete_skill(self, character_id: int, skill_key: int) -> bool:
        """
        Удаление навыка персонажа в рамках переданной сессии.
        """
        stmt = delete(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # flush, но НЕ commit
        if result.rowcount > 0:
            logger.info(f"Навык `{skill_key}` у персонажа `{character_id}` помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Навык `{skill_key}` у персонажа `{character_id}` не найден для удаления.")
            return False

    async def bulk_create_skills(self, character_id: int, skills_data: List[Dict[str, Any]]) -> None:
        """
        Пакетное создание навыков для персонажа в рамках переданной сессии.
        """
        if not skills_data:
            return # Ничего не делаем, если список навыков пуст

        # Подготавливаем список словарей для вставки
        skills_to_insert = []
        for skill_info in skills_data:
            skill_record = {
                "character_id": character_id,
                "skill_key": skill_info.get("skill_key"),
                "level": skill_info.get("level", 0),
                "xp": skill_info.get("xp", 0),
                "progress_state": skill_info.get("progress_state", "PLUS")
            }
            skills_to_insert.append(skill_record)

        # Выполняем пакетную вставку
        stmt = insert(CharacterSkills)
        await self.db_session.execute(stmt, skills_to_insert)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Пакетная вставка {len(skills_to_insert)} навыков для персонажа ID {character_id} добавлена в сессию.")
