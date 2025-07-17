# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/auto_session/xp_tick_data_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, delete, insert

from game_server.database.models.models import XpTickData

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IXpTickDataRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class XpTickDataRepositoryImpl(IXpTickDataRepository):
    """
    Репозиторий для работы с `xp_tick_data` через ORM.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """

    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def bulk_create_xp_data(self, xp_data_list: List[Dict[str, Any]]) -> int:
        """
        Массово создает записи с предрасчитанными данными по опыту за тик в рамках переданной сессии.
        Принимает список словарей, где каждый словарь - данные для одной строки.
        Возвращает количество вставленных строк.
        """
        if not xp_data_list:
            logger.info("Нет данных XP для массовой вставки. Ничего не сделано.")
            return 0

        # SQLAlchemy 2.0 style bulk insert
        result = await self._session.execute(insert(XpTickData), xp_data_list)

        await self._session.flush() # flush, но НЕ commit

        inserted_count = len(xp_data_list)
        logger.info(f"Успешно добавлено {inserted_count} записей XP тиков в сессию.")
        return inserted_count

    async def get_all_xp_data_for_character(self, character_id: int) -> List[XpTickData]:
        """Получает все записи xp_tick_data для конкретного персонажа в рамках переданной сессии."""
        stmt = select(XpTickData).where(XpTickData.character_id == character_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_all_xp_data_for_character(self, character_id: int) -> bool:
        """Удаляет все записи xp_tick_data для конкретного персонажа в рамках переданной сессии."""
        stmt = delete(XpTickData).where(XpTickData.character_id == character_id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Все записи XP тиков для персонажа {character_id} помечены для удаления в сессии.")
            return True
        else:
            logger.warning(f"Записи XP тиков для персонажа {character_id} не найдены для удаления.")
            return False
