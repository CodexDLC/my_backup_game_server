

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select



class ActiveQuestsManager:
    """Менеджер для работы с `active_quests` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_quest(self, character_id: int, quest_id: int, quest_data: dict):
        """Добавление нового квеста."""
        quest = ActiveQuestsManager(character_id=character_id, quest_id=quest_id, **quest_data)
        self.db_session.add(quest)
        await self.db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_data['quest_key']}` добавлен для персонажа `{character_id}`"}

    async def get_quest(self, character_id: int, quest_id: int):
        """Получение квеста по персонажу и ID квеста."""
        query = select(ActiveQuestsManager).where(
            ActiveQuestsManager.character_id == character_id,
            ActiveQuestsManager.quest_id == quest_id
        )
        result = await self.db_session.execute(query)
        row = result.scalar()
        return {"status": "found", "data": row.__dict__} if row else {"status": "error", "message": "Квест не найден"}

    async def update_quest(self, character_id: int, quest_id: int, quest_data: dict):
        """Обновление квеста."""
        query = select(ActiveQuestsManager).where(
            ActiveQuestsManager.character_id == character_id,
            ActiveQuestsManager.quest_id == quest_id
        )
        result = await self.db_session.execute(query)
        quest = result.scalar()

        if quest:
            for key, value in quest_data.items():
                setattr(quest, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Квест `{quest_id}` обновлён для `{character_id}`"}
        return {"status": "error", "message": "Квест не найден"}

    async def delete_quest(self, character_id: int, quest_id: int):
        """Удаление квеста."""
        query = select(ActiveQuestsManager).where(
            ActiveQuestsManager.character_id == character_id,
            ActiveQuestsManager.quest_id == quest_id
        )

        result = await self.db_session.execute(query)
        quest = result.scalar()

        if quest:
            await self.db_session.delete(quest)
            await self.db_session.commit()
            return {"status": "success", "message": f"Квест `{quest_id}` удалён для `{character_id}`"}
        return {"status": "error", "message": "Квест не найден"}
