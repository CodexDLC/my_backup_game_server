

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import Reputation

class ReputationManager:
    """Менеджер для работы с `reputation` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_reputation(self, reputation_id: int, reputation_data: dict):
        """Добавление новой записи о репутации персонажа."""
        reputation = Reputation(reputation_id=reputation_id, **reputation_data)
        self.db_session.add(reputation)
        await self.db_session.commit()
        return {"status": "success", "message": f"Репутация `{reputation_data['reputation_status']}` добавлена персонажу `{reputation_data['character_id']}`"}

    async def get_reputation(self, reputation_id: int):
        """Получение репутации персонажа по ID."""
        query = select(Reputation).where(Reputation.reputation_id == reputation_id)
        result = await self.db_session.execute(query)
        reputation = result.scalar()
        return {"status": "found", "data": reputation.__dict__} if reputation else {"status": "error", "message": "Репутация не найдена"}

    async def update_reputation(self, reputation_id: int, reputation_data: dict):
        """Обновление репутации персонажа."""
        query = select(Reputation).where(Reputation.reputation_id == reputation_id)
        result = await self.db_session.execute(query)
        reputation = result.scalar()

        if reputation:
            for key, value in reputation_data.items():
                setattr(reputation, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Репутация `{reputation_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_reputation(self, reputation_id: int):
        """Удаление записи о репутации."""
        query = select(Reputation).where(Reputation.reputation_id == reputation_id)
        result = await self.db_session.execute(query)
        reputation = result.scalar()

        if reputation:
            await self.db_session.delete(reputation)
            await self.db_session.commit()
            return {"status": "success", "message": f"Репутация `{reputation_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}
