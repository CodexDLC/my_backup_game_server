# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/character_skill_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # <--- ИЗМЕНЕНО: Асинхронная сессия
from sqlalchemy import select, update, delete # Добавлены update, delete
from sqlalchemy.exc import IntegrityError # Для обработки ошибок

# Убедитесь, что путь к вашим моделям корректен
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterSkillRepository
from game_server.database.models.models import CharacterSkills, Skills # У вас также есть Skills

# Импорт интерфейса репозитория


# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class CharacterSkillRepositoryImpl(ICharacterSkillRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью CharacterSkills.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронно).
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_skill(self, character_id: int, skill_data: Dict[str, Any]) -> CharacterSkills: # <--- ИЗМЕНЕНО: async, Dict для данных
        """
        Добавление нового навыка персонажу.
        :param character_id: ID персонажа.
        :param skill_data: Словарь с данными для нового навыка.
        :return: Созданный объект CharacterSkills.
        """
        new_skill = CharacterSkills(character_id=character_id, **skill_data)
        self.db_session.add(new_skill)
        try:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush (вместо commit)
            logger.info(f"Навык '{skill_data.get('skill_key', 'N/A')}' добавлен персонажу {character_id} в сессию.")
            return new_skill
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при создании навыка для персонажа {character_id}: {e.orig}", exc_info=True)
            raise ValueError(f"Навык уже существует или данные некорректны.")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Непредвиденная ошибка при создании навыка для персонажа {character_id}: {e}", exc_info=True)
            raise

    async def get_skill(self, character_id: int, skill_key: int) -> Optional[CharacterSkills]: # <--- ИЗМЕНЕНО: async, возвращает ORM объект
        """
        Получение навыка персонажа.
        """
        stmt = select(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none() # <--- ИЗМЕНЕНО: возвращает ORM объект

    async def update_skill(self, character_id: int, skill_key: int, updates: Dict[str, Any]) -> Optional[CharacterSkills]: # <--- ИЗМЕНЕНО: async, Dict для данных
        """
        Обновление навыка персонажа.
        """
        stmt = update(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        ).values(**updates).returning(CharacterSkills) # <--- ИЗМЕНЕНО: update().values().returning()
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО: await execute
        updated_skill = result.scalars().first()
        if updated_skill:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush
            logger.info(f"Навык `{skill_key}` у персонажа `{character_id}` обновлён в сессии.")
        else:
            logger.warning(f"Навык `{skill_key}` у персонажа `{character_id}` не найден для обновления.")
        return updated_skill # <--- ИЗМЕНЕНО: возвращает ORM объект

    async def delete_skill(self, character_id: int, skill_key: int) -> bool: # <--- ИЗМЕНЕНО: async, возвращает bool
        """
        Удаление навыка персонажа.
        """
        stmt = delete(CharacterSkills).where( # <--- ИЗМЕНЕНО: delete()
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        )
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО: await execute
        await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush
        if result.rowcount > 0:
            logger.info(f"Навык `{skill_key}` у персонажа `{character_id}` помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Навык `{skill_key}` у персонажа `{character_id}` не найден для удаления.")
            return False