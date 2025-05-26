

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import CharactersSpecial, SpecialStatEffects

class CharactersSpecialManager:
    """Менеджер для работы с `characters_special` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_special_stats(self, character_id: int, stats_data: dict):
        """Добавление характеристик персонажа."""
        stats = CharactersSpecial(character_id=character_id, **stats_data)
        self.db_session.add(stats)
        await self.db_session.commit()
        return {"status": "success", "message": f"Характеристики персонажа `{character_id}` записаны"}

    async def get_special_stats(self, character_id: int):
        """Получение характеристик персонажа."""
        query = select(CharactersSpecial).where(CharactersSpecial.character_id == character_id)
        result = await self.db_session.execute(query)
        stats = result.scalar()
        return {"status": "found", "data": stats.__dict__} if stats else {"status": "error", "message": "Персонаж не найден"}

    async def update_special_stats(self, character_id: int, stats_data: dict):
        """Обновление характеристик персонажа."""
        query = select(CharactersSpecial).where(CharactersSpecial.character_id == character_id)
        result = await self.db_session.execute(query)
        stats = result.scalar()

        if stats:
            for key, value in stats_data.items():
                setattr(stats, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Характеристики персонажа `{character_id}` обновлены"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_special_stats(self, character_id: int):
        """Удаление записи о характеристиках персонажа."""
        query = select(CharactersSpecial).where(CharactersSpecial.character_id == character_id)
        result = await self.db_session.execute(query)
        stats = result.scalar()

        if stats:
            await self.db_session.delete(stats)
            await self.db_session.commit()
            return {"status": "success", "message": f"Характеристики персонажа `{character_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}




class SpecialStatEffectsManager:
    """Менеджер для работы с `special_stat_effects` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_effect(self, stat_key: str, effect_data: dict):
        """Добавление нового статового эффекта."""
        effect = SpecialStatEffects(stat_key=stat_key, **effect_data)
        self.db_session.add(effect)
        await self.db_session.commit()
        return {"status": "success", "message": f"Статовый эффект `{stat_key}` добавлен"}

    async def get_effect(self, stat_key: str):
        """Получение статового эффекта."""
        query = select(SpecialStatEffects).where(SpecialStatEffects.stat_key == stat_key)
        result = await self.db_session.execute(query)
        effect = result.scalar()
        return {"status": "found", "data": effect.__dict__} if effect else {"status": "error", "message": "Эффект не найден"}

    async def update_effect(self, stat_key: str, effect_data: dict):
        """Обновление статового эффекта."""
        query = select(SpecialStatEffects).where(SpecialStatEffects.stat_key == stat_key)
        result = await self.db_session.execute(query)
        effect = result.scalar()

        if effect:
            for key, value in effect_data.items():
                setattr(effect, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Статовый эффект `{stat_key}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_effect(self, stat_key: str):
        """Удаление статового эффекта."""
        query = select(SpecialStatEffects).where(SpecialStatEffects.stat_key == stat_key)
        result = await self.db_session.execute(query)
        effect = result.scalar()

        if effect:
            await self.db_session.delete(effect)
            await self.db_session.commit()
            return {"status": "success", "message": f"Статовый эффект `{stat_key}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}
