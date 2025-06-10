from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.database.models.models import ActiveQuests


class ActiveQuestsManager:
    """Менеджер для работы с `active_quests` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_quest(self, character_id: int, quest_id: int, quest_data: dict):
        """Добавление нового квеста."""
        quest = ActiveQuests(character_id=character_id, quest_id=quest_id, **quest_data)
        self.db_session.add(quest)
        await self.db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_data['quest_key']}` добавлен для персонажа `{character_id}`"}

    async def get_quest(self, character_id: int, quest_id: int):
        """Получение квеста по персонажу и ID квеста."""
        query = select(ActiveQuests).where(
            ActiveQuests.character_id == character_id,
            ActiveQuests.quest_id == quest_id
        )
        result = await self.db_session.execute(query)
        row = result.scalar()
        return {"status": "found", "data": row.__dict__} if row else {"status": "error", "message": "Квест не найден"}
