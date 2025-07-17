# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/character_special_repository_impl.py

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, delete

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterSpecialRepository
from game_server.database.models.models import CharacterSpecial

from game_server.config.logging.logging_setup import app_logger as logger


class CharacterSpecialRepositoryImpl(ICharacterSpecialRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью CharacterSpecial.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_special_stats(self, character_id: int, stats_data: Dict[str, Any]) -> CharacterSpecial:
        """
        Добавление характеристик персонажа в рамках переданной сессии.
        Не выполняет commit/rollback.
        """
        new_stats = CharacterSpecial(character_id=character_id, **stats_data)
        self.db_session.add(new_stats)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Характеристики персонажа `{character_id}` записаны в сессию.")
        return new_stats

    async def get_special_stats(self, character_id: int) -> Optional[CharacterSpecial]:
        """
        Получение характеристик персонажа в рамках переданной сессии.
        """
        stmt = select(CharacterSpecial).where(CharacterSpecial.character_id == character_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_special_stats(self, character_id: int, updates: Dict[str, Any]) -> Optional[CharacterSpecial]:
        """
        Обновление характеристик персонажа в рамках переданной сессии.
        Не выполняет commit/rollback.
        """
        stmt = update(CharacterSpecial).where(CharacterSpecial.character_id == character_id).values(**updates).returning(CharacterSpecial)
        result = await self.db_session.execute(stmt)
        updated_stats = result.scalars().first()
        if updated_stats:
            await self.db_session.flush() # flush, но НЕ commit
            logger.info(f"Характеристики персонажа `{character_id}` обновлены в сессии.")
        else:
            logger.warning(f"Характеристики персонажа `{character_id}` не найдены для обновления.")
        return updated_stats

    async def delete_special_stats(self, character_id: int) -> bool:
        """
        Удаление записи о характеристиках персонажа в рамках переданной сессии.
        Не выполняет commit/rollback.
        """
        stmt = delete(CharacterSpecial).where(CharacterSpecial.character_id == character_id)
        result = await self.db_session.execute(stmt)
        if result.rowcount > 0:
            await self.db_session.flush() # flush, но НЕ commit
            logger.info(f"Характеристики персонажа `{character_id}` помечены для удаления в сессии.")
            return True
        else:
            logger.warning(f"Характеристики персонажа `{character_id}` не найдены для удаления.")
            return False
