

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import CharacterExplorationChances




class CharacterExplorationChancesManager:
    """Менеджер для работы с `character_exploration_chances` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_chances(self, character_id: int, chances_data: dict):
        """Добавление новых данных шансов исследования."""
        chances = CharacterExplorationChances(character_id=character_id, **chances_data)
        self.db_session.add(chances)
        await self.db_session.commit()
        return {"status": "success", "message": f"Данные шансов исследования добавлены персонажу {character_id}"}

    async def get_chances(self, character_id: int):
        """Получение данных шансов исследования персонажа."""
        query = select(CharacterExplorationChances).where(CharacterExplorationChances.character_id == character_id)
        result = await self.db_session.execute(query)
        chances = result.scalar()
        return {"status": "found", "data": chances.__dict__} if chances else {"status": "error", "message": "Персонаж не найден"}

    async def update_chances(self, character_id: int, chances_data: dict):
        """Обновление данных шансов исследования."""
        query = select(CharacterExplorationChances).where(CharacterExplorationChances.character_id == character_id)
        result = await self.db_session.execute(query)
        chances = result.scalar()

        if chances:
            for key, value in chances_data.items():
                setattr(chances, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": "Данные шансов исследования обновлены"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_chances(self, character_id: int):
        """Удаление данных шансов исследования."""
        query = select(CharacterExplorationChances).where(CharacterExplorationChances.character_id == character_id)
        result = await self.db_session.execute(query)
        chances = result.scalar()

        if chances:
            await self.db_session.delete(chances)
            await self.db_session.commit()
            return {"status": "success", "message": "Данные шансов исследования удалены"}
        return {"status": "error", "message": "Запись не найдена"}
