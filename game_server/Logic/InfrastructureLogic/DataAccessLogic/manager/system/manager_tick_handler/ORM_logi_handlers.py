
# game_server\Logic\ORM_LOGIC\managers\orm_tick_summary.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import FinishHandler, TickSummary



class TickSummaryManager:
    """Менеджер для работы с `tick_summary` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_tick(self, tick_data: dict):
        """Добавление тик-данных."""
        tick = TickSummary(**tick_data)
        self.db_session.add(tick)
        await self.db_session.commit()
        return {"status": "success", "message": f"Тик-данные для `{tick_data['character_id']}` добавлены"}

    async def get_tick(self, tick_id: int):
        """Получение тик-данных по ID."""
        query = select(TickSummary).where(TickSummary.id == tick_id)
        result = await self.db_session.execute(query)
        tick = result.scalar()
        return {"status": "found", "data": tick.__dict__} if tick else {"status": "error", "message": "Тик-данные не найдены"}

    async def update_tick(self, tick_id: int, tick_data: dict):
        """Обновление тик-данных."""
        query = select(TickSummary).where(TickSummary.id == tick_id)
        result = await self.db_session.execute(query)
        tick = result.scalar()

        if tick:
            for key, value in tick_data.items():
                setattr(tick, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Тик-данные `{tick_id}` обновлены"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_tick(self, tick_id: int):
        """Удаление тик-данных."""
        query = select(TickSummary).where(TickSummary.id == tick_id)
        result = await self.db_session.execute(query)
        tick = result.scalar()

        if tick:
            await self.db_session.delete(tick)
            await self.db_session.commit()
            return {"status": "success", "message": f"Тик-данные `{tick_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}



class FinishHandlerManager:
    """Менеджер для работы с `finish_handlers` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_handler(self, batch_id: str, batch_data: dict):
        """Добавление нового обработчика."""
        handler = FinishHandler(batch_id=batch_id, **batch_data)
        self.db_session.add(handler)
        await self.db_session.commit()
        return {"status": "success", "message": f"Обработчик `{batch_id}` добавлен"}

    async def get_handler(self, batch_id: str):
        """Получение обработчика по batch_id."""
        query = select(FinishHandler).where(FinishHandler.batch_id == batch_id)
        result = await self.db_session.execute(query)
        handler = result.scalar()
        return {"status": "found", "data": handler.__dict__} if handler else {"status": "error", "message": "Обработчик не найден"}

    async def update_handler(self, batch_id: str, batch_data: dict):
        """Обновление обработчика."""
        query = select(FinishHandler).where(FinishHandler.batch_id == batch_id)
        result = await self.db_session.execute(query)
        handler = result.scalar()

        if handler:
            for key, value in batch_data.items():
                setattr(handler, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Обработчик `{batch_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_handler(self, batch_id: str):
        """Удаление обработчика."""
        query = select(FinishHandler).where(FinishHandler.batch_id == batch_id)
        result = await self.db_session.execute(query)
        handler = result.scalar()

        if handler:
            await self.db_session.delete(handler)
            await self.db_session.commit()
            return {"status": "success", "message": f"Обработчик `{batch_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}