# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/auto_session/auto_session_repository_impl.py

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию

# Предполагается, что модель импортируется так
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository
from game_server.database.models.models import AutoSession

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class AutoSessionRepositoryImpl(IAutoSessionRepository):
    """
    Репозиторий для работы с `AutoSession` с гарантией UTC.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """

    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_session(
            self,
            character_id: int,
            active_category: str,
            interval_minutes: int = 6
    ) -> AutoSession:
        """Создаёт сессию с автоматическим расчётом времени в UTC в рамках переданной сессии."""
        now_utc = datetime.now(timezone.utc)
        next_tick_at = now_utc + timedelta(minutes=interval_minutes)

        session_obj = AutoSession(
            character_id=character_id,
            active_category=active_category,
            next_tick_at=next_tick_at,
            last_tick_at=now_utc
        )

        self._session.add(session_obj)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Сессия для персонажа {character_id} (категория: {active_category}) добавлена в сессию.")
        return session_obj

    async def get_session(self, character_id: int) -> Optional[AutoSession]:
        """Получает сессию с проверкой времени UTC в рамках переданной сессии."""
        stmt = select(AutoSession).where(AutoSession.character_id == character_id)
        result = await self._session.execute(stmt)
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
        """Обновляет сессию с приведением времени к UTC в рамках переданной сессии."""
        if 'next_tick_at' in update_data and isinstance(update_data['next_tick_at'], datetime):
            update_data['next_tick_at'] = update_data['next_tick_at'].astimezone(timezone.utc)
        if 'last_tick_at' in update_data and isinstance(update_data['last_tick_at'], datetime):
            update_data['last_tick_at'] = update_data['last_tick_at'].astimezone(timezone.utc)

        stmt = (
            update(AutoSession)
            .where(AutoSession.character_id == character_id)
            .values(**update_data)
            .returning(AutoSession)
        )

        result = await self._session.execute(stmt)
        updated_session = result.scalars().first()

        if updated_session:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Сессия {character_id} обновлена в сессии.")
            return updated_session
        else:
            logger.warning(f"Сессия для персонажа {character_id} не найдена для обновления.")
            return None

    async def delete_session(self, character_id: int) -> bool:
        """Удаляет сессию в рамках переданной сессии."""
        stmt = (
            delete(AutoSession)
            .where(AutoSession.character_id == character_id)
        )

        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Сессия {character_id} помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Сессия {character_id} не найдена для удаления.")
            return False

    async def get_ready_sessions(self) -> List[AutoSession]:
        """Возвращает сессии, готовые к обработке (next_tick_at <= текущее UTC) в рамках переданной сессии."""
        now_utc = datetime.now(timezone.utc)
        stmt = (
            select(AutoSession)
            .where(AutoSession.next_tick_at <= now_utc)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_character_tick_time(
            self,
            character_id: int,
            interval_minutes: int = 6
    ) -> Optional[AutoSession]:
        """
        Специализированный метод для обновления времени тика в рамках переданной сессии.
        Устанавливает last_tick_at на текущее время UTC и рассчитывает next_tick_at.
        """
        now_utc = datetime.now(timezone.utc)
        next_tick_at = now_utc + timedelta(minutes=interval_minutes)

        stmt = (
            update(AutoSession)
            .where(AutoSession.character_id == character_id)
            .values(
                last_tick_at=now_utc,
                next_tick_at=next_tick_at
            ).returning(AutoSession)
        )

        result = await self._session.execute(stmt)
        updated_session = result.scalars().first()

        if updated_session:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Время тика для сессии {character_id} обновлено в сессии.")
            return updated_session
        else:
            logger.warning(f"Сессия для персонажа {character_id} не найдена для обновления времени тика.")
            return None
