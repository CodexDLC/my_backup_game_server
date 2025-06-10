

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import CharactersSpecial, SpecialStatEffect


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




class SpecialStatEffectManager:
    """
    Менеджер для управления объектами SpecialStatEffect в базе данных (асинхронный).
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_effect_by_id(self, effect_id: int) -> Optional[SpecialStatEffect]:
        """Получает эффект по его ID."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.effect_id == effect_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_effect_by_keys(self, stat_key: str, affected_property: str, effect_type: str) -> Optional[SpecialStatEffect]:
        """Получает эффект по комбинации stat_key, affected_property и effect_type."""
        stmt = select(SpecialStatEffect).where(
            SpecialStatEffect.stat_key == stat_key,
            SpecialStatEffect.affected_property == affected_property,
            SpecialStatEffect.effect_type == effect_type
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_effects_for_stat(self, stat_key: str) -> List[SpecialStatEffect]:
        """Возвращает все эффекты, связанные с конкретной характеристикой."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.stat_key == stat_key)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_effects_for_property(self, affected_property: str) -> List[SpecialStatEffect]:
        """Возвращает все эффекты, влияющие на конкретное свойство."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.affected_property == affected_property)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_effect(self, effect: SpecialStatEffect) -> SpecialStatEffect:
        """Создает новый эффект в базе данных."""
        self.db.add(effect)
        await self.db.commit()
        await self.db.refresh(effect)
        return effect

    async def update_effect(self, effect: SpecialStatEffect) -> bool:
        """Обновляет существующий эффект."""
        existing_effect = await self.get_effect_by_id(effect.effect_id)
        if existing_effect:
            existing_effect.stat_key = effect.stat_key
            existing_effect.affected_property = effect.affected_property
            existing_effect.effect_type = effect.effect_type
            existing_effect.value = effect.value
            existing_effect.calculation_order = effect.calculation_order
            existing_effect.description = effect.description
            await self.db.commit()
            return True
        return False

    async def delete_effect(self, effect_id: int) -> bool:
        """Удаляет эффект по его ID."""
        effect_to_delete = await self.get_effect_by_id(effect_id)
        if effect_to_delete:
            await self.db.delete(effect_to_delete)
            await self.db.commit()
            return True
        return False