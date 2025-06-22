# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/skill_exclusion_repository_impl.py

import logging
from typing import List, Optional, Dict, Any # Добавлено Dict, Any для update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete # Добавлены update, delete
from sqlalchemy.exc import IntegrityError # На всякий случай

# Убедитесь, что путь к вашей модели SkillExclusion корректен
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ISkillExclusionRepository
from game_server.database.models.models import SkillExclusion

# Импорт интерфейса репозитория


# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class SkillExclusionRepositoryImpl(ISkillExclusionRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью SkillExclusion.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронный).
    """
    def __init__(self, db: AsyncSession): # Изменено 'db' на 'db_session' для консистентности
        self.db_session = db # Использование db_session

    async def get_exclusion_by_id(self, exclusion_id: int) -> Optional[SkillExclusion]:
        """Получает правило исключения по его ID."""
        stmt = select(SkillExclusion).where(SkillExclusion.exclusion_id == exclusion_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_exclusion_by_group_name(self, group_name: str) -> Optional[SkillExclusion]:
        """Получает правило исключения по названию группы."""
        stmt = select(SkillExclusion).where(SkillExclusion.group_name == group_name)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_exclusions(self) -> List[SkillExclusion]:
        """Возвращает все правила исключений навыков."""
        stmt = select(SkillExclusion)
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def create_exclusion(self, exclusion_data: Dict[str, Any]) -> SkillExclusion: # <--- ИЗМЕНЕНО: exclusion на exclusion_data (Dict)
        """Создает новое правило исключения навыков в базе данных."""
        new_exclusion = SkillExclusion(**exclusion_data) # <--- ИЗМЕНЕНО
        self.db_session.add(new_exclusion)
        try:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush
            logger.info(f"Правило исключения (группа: {exclusion_data.get('group_name', 'N/A')}) создано в сессии.")
            return new_exclusion
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при создании правила исключения: {e.orig}", exc_info=True)
            raise ValueError(f"Правило исключения с такими параметрами уже существует.")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Непредвиденная ошибка при создании правила исключения: {e}", exc_info=True)
            raise

    async def update_exclusion(self, exclusion_id: int, updates: Dict[str, Any]) -> Optional[SkillExclusion]: # <--- ИЗМЕНЕНО: exclusion на exclusion_id, updates
        """Обновляет существующее правило исключения навыков."""
        stmt = update(SkillExclusion).where(SkillExclusion.exclusion_id == exclusion_id).values(**updates).returning(SkillExclusion) # <--- ИЗМЕНЕНО
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        updated_exclusion = result.scalars().first()
        if updated_exclusion:
            await self.db_session.flush() # <--- ИЗМЕНЕНО
            logger.info(f"Правило исключения (ID: {exclusion_id}) обновлено в сессии.")
            return updated_exclusion
        else:
            logger.warning(f"Правило исключения с ID {exclusion_id} не найдено для обновления.")
            return None

    async def delete_exclusion(self, exclusion_id: int) -> bool: # <--- ИЗМЕНЕНО
        """Удаляет правило исключения навыков по его ID."""
        stmt = delete(SkillExclusion).where(SkillExclusion.exclusion_id == exclusion_id) # <--- ИЗМЕНЕНО
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        if result.rowcount > 0:
            await self.db_session.flush() # <--- ИЗМЕНЕНО
            logger.info(f"Правило исключения (ID: {exclusion_id}) помечено для удаления в сессии.")
            return True
        else:
            logger.warning(f"Правило исключения с ID {exclusion_id} не найдено для удаления.")
            return False