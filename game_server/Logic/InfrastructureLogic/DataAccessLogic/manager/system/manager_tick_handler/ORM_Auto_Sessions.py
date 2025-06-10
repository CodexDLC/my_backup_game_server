from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Предполагается, что модель импортируется так
from game_server.database.models.models import AutoSession


class AutoSessionsManager:
    """Менеджер для работы с `auto_sessions` с гарантией UTC."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_session(
            self,
            character_id: int,
            active_category: str,
            interval_minutes: int = 6
    ) -> Dict[str, Any]:
        """Создаёт сессию с автоматическим расчётом времени в UTC."""
        now_utc = datetime.now(timezone.utc)
        next_tick_at = now_utc + timedelta(minutes=interval_minutes)

        session = AutoSession(
            character_id=character_id,
            active_category=active_category,
            next_tick_at=next_tick_at,
            last_tick_at=now_utc
        )

        self.db_session.add(session)
        try:
            await self.db_session.commit()
            return {
                "status": "success",
                "data": {
                    "character_id": character_id,
                    "next_tick_at": next_tick_at.isoformat()
                }
            }
        except Exception as e:
            await self.db_session.rollback()
            return {"status": "error", "message": f"Ошибка создания сессии: {str(e)}"}

    async def get_session(self, character_id: int) -> Optional[Dict[str, Any]]:
        """Получает сессию с проверкой времени UTC."""
        result = await self.db_session.execute(
            select(AutoSession).where(AutoSession.character_id == character_id))
        session = result.scalar()

        if not session:
            return None

        return {
            "character_id": session.character_id,
            "active_category": session.active_category,
            "next_tick_at": session.next_tick_at.replace(tzinfo=timezone.utc),
            "last_tick_at": session.last_tick_at.replace(tzinfo=timezone.utc)
        }

    async def update_session(
            self,
            character_id: int,
            update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обновляет сессию с приведением времени к UTC."""
        if 'next_tick_at' in update_data and isinstance(update_data['next_tick_at'], datetime):
            update_data['next_tick_at'] = update_data['next_tick_at'].astimezone(timezone.utc)

        await self.db_session.execute(
            update(AutoSession)
            .where(AutoSession.character_id == character_id)
            .values(**update_data)
        )

        try:
            await self.db_session.commit()
            return {"status": "success", "message": f"Сессия {character_id} обновлена"}
        except Exception as e:
            await self.db_session.rollback()
            return {"status": "error", "message": f"Ошибка обновления: {str(e)}"}

    async def delete_session(self, character_id: int) -> Dict[str, Any]:
        """Удаляет сессию с обработкой ошибок."""
        await self.db_session.execute(
            delete(AutoSession)
            .where(AutoSession.character_id == character_id)
        )

        try:
            await self.db_session.commit()
            return {"status": "success", "message": f"Сессия {character_id} удалена"}
        except Exception as e:
            await self.db_session.rollback()
            return {"status": "error", "message": f"Ошибка удаления: {str(e)}"}

    async def get_ready_sessions(self) -> list:
        """Возвращает сессии, готовые к обработке (next_tick_at <= текущее UTC)."""
        now_utc = datetime.now(timezone.utc)
        result = await self.db_session.execute(
            select(AutoSession)
            .where(AutoSession.next_tick_at <= now_utc)
        )
        return result.scalars().all()

    # --- НОВЫЙ МЕТОД ---
    async def update_character_tick_time(
            self,
            character_id: int,
            interval_minutes: int = 6
    ) -> Dict[str, Any]:
        """
        Специализированный метод для обновления времени тика.
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
            )
        )

        try:
            result = await self.db_session.execute(stmt)
            
            # Проверяем, была ли действительно обновлена строка
            if result.rowcount == 0:
                await self.db_session.rollback()
                return {"status": "error", "message": f"Сессия для персонажа {character_id} не найдена."}

            await self.db_session.commit()
            return {"status": "success", "message": f"Время тика для сессии {character_id} обновлено."}

        except Exception as e:
            await self.db_session.rollback()
            return {"status": "error", "message": f"Ошибка обновления времени тика: {str(e)}"}