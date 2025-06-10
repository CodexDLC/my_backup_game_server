from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from game_server.database.models.models import SkillExclusion

# Убедитесь, что SkillExclusion импортирован из вашего файла моделей


class SkillExclusionManager:
    """
    Менеджер для управления объектами SkillExclusion в базе данных (асинхронный).
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_exclusion_by_id(self, exclusion_id: int) -> Optional[SkillExclusion]:
        """Получает правило исключения по его ID."""
        stmt = select(SkillExclusion).where(SkillExclusion.exclusion_id == exclusion_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_exclusion_by_group_name(self, group_name: str) -> Optional[SkillExclusion]:
        """Получает правило исключения по названию группы."""
        stmt = select(SkillExclusion).where(SkillExclusion.group_name == group_name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_exclusions(self) -> List[SkillExclusion]:
        """Возвращает все правила исключений навыков."""
        stmt = select(SkillExclusion)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_exclusion(self, exclusion: SkillExclusion) -> SkillExclusion:
        """Создает новое правило исключения навыков в базе данных."""
        self.db.add(exclusion)
        await self.db.commit()
        await self.db.refresh(exclusion)
        return exclusion

    async def update_exclusion(self, exclusion: SkillExclusion) -> bool:
        """Обновляет существующее правило исключения навыков."""
        existing_exclusion = await self.get_exclusion_by_id(exclusion.exclusion_id)
        if existing_exclusion:
            existing_exclusion.group_name = exclusion.group_name
            existing_exclusion.description = exclusion.description
            existing_exclusion.exclusion_type = exclusion.exclusion_type
            existing_exclusion.excluded_skills = exclusion.excluded_skills
            existing_exclusion.exclusion_effect = exclusion.exclusion_effect
            await self.db.commit()
            return True
        return False

    async def delete_exclusion(self, exclusion_id: int) -> bool:
        """Удаляет правило исключения навыков по его ID."""
        exclusion_to_delete = await self.get_exclusion_by_id(exclusion_id)
        if exclusion_to_delete:
            await self.db.delete(exclusion_to_delete)
            await self.db.commit()
            return True
        return False