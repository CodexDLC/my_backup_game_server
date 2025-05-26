

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import Bloodlines, Characters, Races

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




class BloodlinesManager:
    """Менеджер для работы с `bloodlines` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_bloodline(self, bloodline_data: dict):
        """Добавление новой родословной."""
        bloodline = Bloodlines(**bloodline_data)
        self.db_session.add(bloodline)
        await self.db_session.commit()
        return {"status": "success", "message": f"Родословная `{bloodline_data['bloodline_name']}` добавлена"}

    async def get_bloodline(self, bloodline_id: int):
        """Получение родословной по ID."""
        query = select(Bloodlines).where(Bloodlines.bloodline_id == bloodline_id)
        result = await self.db_session.execute(query)
        bloodline = result.scalar()
        return {"status": "found", "data": bloodline.__dict__} if bloodline else {"status": "error", "message": "Родословная не найдена"}

    async def update_bloodline(self, bloodline_id: int, bloodline_data: dict):
        """Обновление данных родословной."""
        query = select(Bloodlines).where(Bloodlines.bloodline_id == bloodline_id)
        result = await self.db_session.execute(query)
        bloodline = result.scalar()

        if bloodline:
            for key, value in bloodline_data.items():
                setattr(bloodline, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Родословная `{bloodline_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_bloodline(self, bloodline_id: int):
        """Удаление родословной."""
        query = select(Bloodlines).where(Bloodlines.bloodline_id == bloodline_id)
        result = await self.db_session.execute(query)
        bloodline = result.scalar()

        if bloodline:
            await self.db_session.delete(bloodline)
            await self.db_session.commit()
            return {"status": "success", "message": f"Родословная `{bloodline_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}
    



class RacesManager:
    """Менеджер для работы с `races` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_race(self, race_data: dict):
        """Добавление новой расы."""
        race = Races(**race_data)
        self.db_session.add(race)
        await self.db_session.commit()
        return {"status": "success", "message": f"Раса `{race_data['name']}` добавлена"}

    async def get_race(self, race_id: int):
        """Получение расы по ID."""
        query = select(Races).where(Races.race_id == race_id)
        result = await self.db_session.execute(query)
        race = result.scalar()
        return {"status": "found", "data": race.__dict__} if race else {"status": "error", "message": "Раса не найдена"}

    async def update_race(self, race_id: int, race_data: dict):
        """Обновление данных расы."""
        query = select(Races).where(Races.race_id == race_id)
        result = await self.db_session.execute(query)
        race = result.scalar()

        if race:
            for key, value in race_data.items():
                setattr(race, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Раса `{race_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_race(self, race_id: int):
        """Удаление расы."""
        query = select(Races).where(Races.race_id == race_id)
        result = await self.db_session.execute(query)
        race = result.scalar()

        if race:
            await self.db_session.delete(race)
            await self.db_session.commit()
            return {"status": "success", "message": f"Раса `{race_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}