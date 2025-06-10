from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from game_server.database.models.models import Ability # Для загрузки связанных данных

# Убедитесь, что Ability и Skill импортированы из вашего файла моделей

class AbilityManager:
    """
    Менеджер для управления объектами Ability в базе данных (асинхронный).
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ability_by_id(self, ability_id: int) -> Optional[Ability]:
        """Получает способность по её ID."""
        stmt = select(Ability).where(Ability.ability_id == ability_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_ability_by_key(self, ability_key: str) -> Optional[Ability]:
        """Получает способность по её строковому ключу."""
        stmt = select(Ability).where(Ability.ability_key == ability_key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_abilities(self) -> List[Ability]:
        """Возвращает все способности."""
        stmt = select(Ability)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_ability(self, ability: Ability) -> Ability:
        """Создает новую способность в базе данных."""
        self.db.add(ability)
        await self.db.commit()
        await self.db.refresh(ability)
        return ability

    async def update_ability(self, ability: Ability) -> bool:
        """Обновляет существующую способность."""
        existing_ability = await self.get_ability_by_id(ability.ability_id)
        if existing_ability:
            existing_ability.name = ability.name
            existing_ability.description = ability.description
            existing_ability.ability_type = ability.ability_type
            existing_ability.required_skill_key = ability.required_skill_key
            existing_ability.required_skill_level = ability.required_skill_level
            existing_ability.required_stats = ability.required_stats
            existing_ability.required_items = ability.required_items
            existing_ability.cost_type = ability.cost_type
            existing_ability.cost_amount = ability.cost_amount
            existing_ability.cooldown_seconds = ability.cooldown_seconds
            existing_ability.cast_time_ms = ability.cast_time_ms
            existing_ability.effect_data = ability.effect_data
            existing_ability.animation_key = ability.animation_key
            existing_ability.sfx_key = ability.sfx_key
            existing_ability.vfx_key = ability.vfx_key
            await self.db.commit()
            return True
        return False

    async def delete_ability(self, ability_id: int) -> bool:
        """Удаляет способность по её ID."""
        ability_to_delete = await self.get_ability_by_id(ability_id)
        if ability_to_delete:
            await self.db.delete(ability_to_delete)
            await self.db.commit()
            return True
        return False

    async def get_ability_with_skill_requirement(self, ability_key: str) -> Optional[Ability]:
        """Получает способность с загруженными данными о требуемом навыке."""
        stmt = select(Ability).where(Ability.ability_key == ability_key).options(
            selectinload(Ability.skill_requirement)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()