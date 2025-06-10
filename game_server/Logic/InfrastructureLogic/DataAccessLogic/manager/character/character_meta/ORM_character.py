

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import Bloodline, Bloodlines, Characters, Races



class CharactersManager:
    """Менеджер для работы с `characters` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_character(self, account_id: int):
        """Создание нового персонажа."""
        new_character = Characters(
            account_id=account_id,
            name="Безымянный",
            surname=None,
            bloodline_id=None,
            race_id=1,
            is_deleted=False
        )
        self.db_session.add(new_character)
        await self.db_session.commit()
        return {"status": "success", "character_id": new_character.character_id}

    async def get_character(self, character_id: int):
        """Получение персонажа по ID."""
        query = select(Characters).where(Characters.character_id == character_id)
        result = await self.db_session.execute(query)
        character = result.scalar()
        return {"status": "found", "data": character.__dict__} if character else {"status": "error", "message": "Персонаж не найден"}

    async def update_character(self, character_id: int, character_data: dict):
        """Обновление данных персонажа."""
        query = select(Characters).where(Characters.character_id == character_id)
        result = await self.db_session.execute(query)
        character = result.scalar()

        if character:
            for key, value in character_data.items():
                setattr(character, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": "Персонаж обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_character(self, character_id: int):
        """Логическое удаление персонажа."""
        query = select(Characters).where(Characters.character_id == character_id)
        result = await self.db_session.execute(query)
        character = result.scalar()

        if character:
            character.is_deleted = True
            await self.db_session.commit()
            return {"status": "success", "message": "Персонаж удалён"}
        return {"status": "error", "message": "Запись не найдена"}




