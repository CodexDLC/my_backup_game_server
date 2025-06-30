# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/auto_session/auto_session_repository_impl.py

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Type # Добавлен Type
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# Предполагается, что модель импортируется так
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository
from game_server.database.models.models import AutoSession

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class AutoSessionRepositoryImpl(IAutoSessionRepository):
    """
    Репозиторий для работы с `AutoSession` с гарантией UTC.
    """

    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create_session(
            self,
            character_id: int,
            active_category: str,
            interval_minutes: int = 6
    ) -> AutoSession:
        """Создаёт сессию с автоматическим расчётом времени в UTC."""
        now_utc = datetime.now(timezone.utc)
        next_tick_at = now_utc + timedelta(minutes=interval_minutes)

        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            session_obj = AutoSession(
                character_id=character_id,
                active_category=active_category,
                next_tick_at=next_tick_at,
                last_tick_at=now_utc
            )

            session.add(session_obj)
            try:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Сессия для персонажа {character_id} (категория: {active_category}) создана в БД.")
                return session_obj
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании сессии для персонажа {character_id}: {e.orig}", exc_info=True)
                raise ValueError(f"Сессия для персонажа {character_id} уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании сессии для персонажа {character_id}: {e}", exc_info=True)
                raise

    async def get_session(self, character_id: int) -> Optional[AutoSession]:
        """Получает сессию с проверкой времени UTC."""
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = select(AutoSession).where(AutoSession.character_id == character_id)
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            session_obj = result.scalar_one_or_none()

            if not session_obj:
                logger.debug(f"Сессия для персонажа {character_id} не найдена.")
                return None
            return session_obj

    async def update_session(
            self,
            character_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[AutoSession]:
        """Обновляет сессию с приведением времени к UTC."""
        if 'next_tick_at' in update_data and isinstance(update_data['next_tick_at'], datetime):
            update_data['next_tick_at'] = update_data['next_tick_at'].astimezone(timezone.utc)
        if 'last_tick_at' in update_data and isinstance(update_data['last_tick_at'], datetime):
            update_data['last_tick_at'] = update_data['last_tick_at'].astimezone(timezone.utc)

        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = (
                update(AutoSession)
                .where(AutoSession.character_id == character_id)
                .values(**update_data)
                .returning(AutoSession)
            )

            try:
                result = await session.execute(stmt) # ИСПРАВЛЕНО
                updated_session = result.scalars().first()

                if updated_session:
                    await session.flush()
                    await session.commit() # ДОБАВЛЕНО commit
                    logger.info(f"Сессия {character_id} обновлена в БД.")
                    return updated_session
                else:
                    await session.rollback() # ДОБАВЛЕНО rollback
                    logger.warning(f"Сессия для персонажа {character_id} не найдена для обновления.")
                    return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка обновления сессии {character_id}: {str(e)}", exc_info=True)
                raise

    async def delete_session(self, character_id: int) -> bool:
        """Удаляет сессию с обработкой ошибок."""
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = (
                delete(AutoSession)
                .where(AutoSession.character_id == character_id)
            )

            try:
                result = await session.execute(stmt) # ИСПРАВЛЕНО
                if result.rowcount > 0:
                    await session.flush()
                    await session.commit() # ДОБАВЛЕНО commit
                    logger.info(f"Сессия {character_id} удалена из БД.")
                    return True
                else:
                    await session.rollback() # ДОБАВЛЕНО rollback
                    logger.warning(f"Сессия {character_id} не найдена для удаления.")
                    return False
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка удаления сессии {character_id}: {str(e)}", exc_info=True)
                raise

    async def get_ready_sessions(self) -> List[AutoSession]:
        """Возвращает сессии, готовые к обработке (next_tick_at <= текущее UTC)."""
        now_utc = datetime.now(timezone.utc)
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = (
                select(AutoSession)
                .where(AutoSession.next_tick_at <= now_utc)
            )
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            return list(result.scalars().all())

    async def update_character_tick_time(
            self,
            character_id: int,
            interval_minutes: int = 6
    ) -> Optional[AutoSession]:
        """
        Специализированный метод для обновления времени тика.
        Устанавливает last_tick_at на текущее время UTC и рассчитывает next_tick_at.
        """
        now_utc = datetime.now(timezone.utc)
        next_tick_at = now_utc + timedelta(minutes=interval_minutes)

        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = (
                update(AutoSession)
                .where(AutoSession.character_id == character_id)
                .values(
                    last_tick_at=now_utc,
                    next_tick_at=next_tick_at
                ).returning(AutoSession)
            )

            try:
                result = await session.execute(stmt) # ИСПРАВЛЕНО
                updated_session = result.scalars().first()

                if updated_session:
                    await session.flush()
                    await session.commit() # ДОБАВЛЕНО commit
                    logger.info(f"Время тика для сессии {character_id} обновлено в БД.")
                    return updated_session
                else:
                    await session.rollback() # ДОБАВЛЕНО rollback
                    logger.warning(f"Сессия для персонажа {character_id} не найдена для обновления времени тика.")
                    return None

            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка обновления времени тика для сессии {character_id}: {str(e)}", exc_info=True)
                raise
