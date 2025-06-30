# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/auto_session/xp_tick_data_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from sqlalchemy.exc import IntegrityError # Добавлен импорт

from game_server.database.models.models import XpTickData # Убедитесь, что модели импортированы правильно

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IXpTickDataRepository # <--- ИМПОРТ ИНТЕРФЕЙСА

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class XpTickDataRepositoryImpl(IXpTickDataRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для работы с `xp_tick_data` через ORM.
    """

    def __init__(self, db_session: AsyncSession): # <--- ИЗМЕНЕНО: Используем db_session для консистентности
        self.db_session = db_session # <--- ИЗМЕНЕНО: Используем db_session

    async def bulk_create_xp_data(self, xp_data_list: List[Dict[str, Any]]) -> int: # <--- ИЗМЕНЕНО: возвращает int (количество вставленных строк)
        """
        Массово создает записи с предрасчитанными данными по опыту за тик.
        Принимает список словарей, где каждый словарь - данные для одной строки.
        Возвращает количество вставленных строк.
        """
        if not xp_data_list:
            logger.info("Нет данных XP для массовой вставки.")
            return 0

        try:
            # SQLAlchemy 2.0 style bulk insert
            result = await self.db_session.execute(insert(XpTickData), xp_data_list) # <--- ИЗМЕНЕНО: self.db_session

            # Так как insert не возвращает объекты, мы не можем вернуть их напрямую.
            # Возвращаем rowcount, если это возможно, или 0, если нет прямого метода
            # Для insert (on_conflict_do_nothing) result.rowcount может быть 0
            await self.db_session.flush() # <--- ИЗМЕНЕНО: flush

            # result.rowcount для bulk insert часто 1, т.к. это один execute.
            # Для получения точного количества вставленных/обновленных строк,
            # нужно использовать returning() или делать select после.
            # Если важен только факт успешной вставки, можно просто True.
            # Для простоты, возвращаем количество переданных элементов, если нет ошибок.
            inserted_count = len(xp_data_list)
            logger.info(f"Успешно добавлено {inserted_count} записей XP тиков в сессию.")
            return inserted_count
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при массовой вставке данных XP тиков: {e.orig}", exc_info=True)
            raise ValueError("Ошибка целостности при массовой вставке XP тиков.")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Непредвиденная ошибка при массовой вставке данных XP тиков: {e}", exc_info=True)
            raise

    async def get_all_xp_data_for_character(self, character_id: int) -> List[XpTickData]:
        """Получает все записи xp_tick_data для конкретного персонажа."""
        stmt = select(XpTickData).where(XpTickData.character_id == character_id)
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО: self.db_session
        return list(result.scalars().all())

    async def delete_all_xp_data_for_character(self, character_id: int) -> bool: # <--- ИЗМЕНЕНО: возвращает bool
        """Удаляет все записи xp_tick_data для конкретного персонажа."""
        stmt = delete(XpTickData).where(XpTickData.character_id == character_id)
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО: self.db_session
        if result.rowcount > 0:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: flush
            logger.info(f"Все записи XP тиков для персонажа {character_id} помечены для удаления в сессии.")
            return True
        else:
            logger.warning(f"Записи XP тиков для персонажа {character_id} не найдены для удаления.")
            return False