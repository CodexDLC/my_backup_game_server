# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/skill_exclusion_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

# Убедитесь, что путь к вашей модели SkillExclusion корректен
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ISkillExclusionRepository
from game_server.database.models.models import SkillExclusion

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class SkillExclusionRepositoryImpl(ISkillExclusionRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью SkillExclusion.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def get_exclusion_by_id(self, exclusion_id: int) -> Optional[SkillExclusion]:
        """Получает правило исключения по его ID в рамках переданной сессии."""
        stmt = select(SkillExclusion).where(SkillExclusion.exclusion_id == exclusion_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_exclusion_by_group_name(self, group_name: str) -> Optional[SkillExclusion]:
        """Получает правило исключения по названию группы в рамках переданной сессии."""
        stmt = select(SkillExclusion).where(SkillExclusion.group_name == group_name)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_exclusions(self) -> List[SkillExclusion]:
        """Возвращает все правила исключений навыков в рамках переданной сессии."""
        stmt = select(SkillExclusion)
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def create_exclusion(self, exclusion_data: Dict[str, Any]) -> SkillExclusion:
        """Создает новое правило исключения навыков в рамках переданной сессии."""
        new_exclusion = SkillExclusion(**exclusion_data)
        self.db_session.add(new_exclusion)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Правило исключения (группа: {exclusion_data.get('group_name', 'N/A')}) создано в сессии.")
        return new_exclusion

    async def update_exclusion(self, exclusion_id: int, updates: Dict[str, Any]) -> Optional[SkillExclusion]:
        """Обновляет существующее правило исключения навыков в рамках переданной сессии."""
        stmt = update(SkillExclusion).where(SkillExclusion.exclusion_id == exclusion_id).values(**updates).returning(SkillExclusion)
        result = await self.db_session.execute(stmt)
        updated_exclusion = result.scalars().first()
        if updated_exclusion:
            await self.db_session.flush() # flush, но НЕ commit
            logger.info(f"Правило исключения (ID: {exclusion_id}) обновлено в сессии.")
            return updated_exclusion
        else:
            logger.warning(f"Правило исключения с ID {exclusion_id} не найдено для обновления.")
            return None

    async def delete_exclusion(self, exclusion_id: int) -> bool:
        """Удаляет правило исключения навыков по его ID в рамках переданной сессии."""
        stmt = delete(SkillExclusion).where(SkillExclusion.exclusion_id == exclusion_id)
        result = await self.db_session.execute(stmt)
        if result.rowcount > 0:
            await self.db_session.flush() # flush, но НЕ commit
            logger.info(f"Правило исключения (ID: {exclusion_id}) помечено для удаления в сессии.")
            return True
        else:
            logger.warning(f"Правило исключения с ID {exclusion_id} не найдено для удаления.")
            return False
