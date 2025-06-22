# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/character_special_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # <--- ИЗМЕНЕНО: Асинхронная сессия
from sqlalchemy import select, update, delete # Добавлены update, delete
from sqlalchemy.exc import IntegrityError

# Убедитесь, что путь к вашим моделям корректен
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterSpecialRepository
from game_server.database.models.models import CharacterSpecial, SpecialStatEffect # SpecialStatEffect здесь не нужен, но был в оригинале

# Импорт интерфейса репозитория


# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class CharacterSpecialRepositoryImpl(ICharacterSpecialRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью CharacterSpecial.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронно).
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_special_stats(self, character_id: int, stats_data: Dict[str, Any]) -> CharacterSpecial: # <--- ИЗМЕНЕНО: async, Dict для данных
        """
        Добавление характеристик персонажа.
        """
        new_stats = CharacterSpecial(character_id=character_id, **stats_data)
        self.db_session.add(new_stats)
        try:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush (вместо commit)
            logger.info(f"Характеристики персонажа `{character_id}` записаны в сессию.")
            return new_stats
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при создании характеристик для персонажа {character_id}: {e.orig}", exc_info=True)
            raise ValueError(f"Характеристики для персонажа уже существуют или данные некорректны.")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Непредвиденная ошибка при создании характеристик для персонажа {character_id}: {e}", exc_info=True)
            raise

    async def get_special_stats(self, character_id: int) -> Optional[CharacterSpecial]: # <--- ИЗМЕНЕНО: async, возвращает ORM объект
        """
        Получение характеристик персонажа.
        """
        stmt = select(CharacterSpecial).where(CharacterSpecial.character_id == character_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_special_stats(self, character_id: int, updates: Dict[str, Any]) -> Optional[CharacterSpecial]: # <--- ИЗМЕНЕНО: async, Dict для данных
        """
        Обновление характеристик персонажа.
        """
        stmt = update(CharacterSpecial).where(CharacterSpecial.character_id == character_id).values(**updates).returning(CharacterSpecial)
        result = await self.db_session.execute(stmt)
        updated_stats = result.scalars().first()
        if updated_stats:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush
            logger.info(f"Характеристики персонажа `{character_id}` обновлены в сессии.")
        else:
            logger.warning(f"Характеристики персонажа `{character_id}` не найдены для обновления.")
        return updated_stats

    async def delete_special_stats(self, character_id: int) -> bool: # <--- ИЗМЕНЕНО: async, возвращает bool
        """
        Удаление записи о характеристиках персонажа.
        """
        stmt = delete(CharacterSpecial).where(CharacterSpecial.character_id == character_id)
        result = await self.db_session.execute(stmt)
        if result.rowcount > 0:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush
            logger.info(f"Характеристики персонажа `{character_id}` помечены для удаления в сессии.")
            return True
        else:
            logger.warning(f"Характеристики персонажа `{character_id}` не найдены для удаления.")
            return False