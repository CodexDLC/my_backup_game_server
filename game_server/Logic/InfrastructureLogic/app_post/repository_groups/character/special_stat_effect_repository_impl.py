# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/special_stat_effect_repository_impl.py

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete # Добавлены update, delete
from sqlalchemy.exc import IntegrityError
# Убедитесь, что путь к вашей модели SkillExclusion корректен
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ISpecialStatEffectRepository
from game_server.database.models.models import SpecialStatEffect # <--- ОБРАТИТЕ ВНИМАНИЕ: модель SpecialStatEffect

# Импорт интерфейса репозитория


# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class SpecialStatEffectRepositoryImpl(ISpecialStatEffectRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью SpecialStatEffect.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронный).
    """
    def __init__(self, db: AsyncSession): # Изменено 'db' на 'db_session' для консистентности
        self.db_session = db # Использование db_session

    async def get_effect_by_id(self, effect_id: int) -> Optional[SpecialStatEffect]:
        """Получает эффект по его ID."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.effect_id == effect_id)
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        return result.scalar_one_or_none()

    async def get_effect_by_keys(self, stat_key: str, affected_property: str, effect_type: str) -> Optional[SpecialStatEffect]:
        """Получает эффект по комбинации stat_key, affected_property и effect_type."""
        stmt = select(SpecialStatEffect).where(
            SpecialStatEffect.stat_key == stat_key,
            SpecialStatEffect.affected_property == affected_property,
            SpecialStatEffect.effect_type == effect_type
        )
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        return result.scalar_one_or_none()

    async def get_effects_for_stat(self, stat_key: str) -> List[SpecialStatEffect]:
        """Возвращает все эффекты, связанные с конкретной характеристикой."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.stat_key == stat_key)
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        return result.scalars().all()

    async def get_effects_for_property(self, affected_property: str) -> List[SpecialStatEffect]:
        """Возвращает все эффекты, влияющие на конкретное свойство."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.affected_property == affected_property)
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        return result.scalars().all()

    async def create_effect(self, effect_data: Dict[str, Any]) -> SpecialStatEffect: # <--- ИЗМЕНЕНО: effect на effect_data
        """Создает новый эффект в базе данных."""
        new_effect = SpecialStatEffect(**effect_data) # <--- ИЗМЕНЕНО
        self.db_session.add(new_effect)
        try:
            await self.db_session.flush() # <--- ИЗМЕНЕНО
            logger.info(f"Эффект '{effect_data.get('stat_key', 'N/A')}' создан в сессии.")
            return new_effect
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при создании эффекта: {e.orig}", exc_info=True)
            raise ValueError(f"Эффект с такими параметрами уже существует.")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Непредвиденная ошибка при создании эффекта: {e}", exc_info=True)
            raise

    async def update_effect(self, effect_id: int, updates: Dict[str, Any]) -> Optional[SpecialStatEffect]: # <--- ИЗМЕНЕНО: effect на effect_id, updates
        """Обновляет существующий эффект."""
        stmt = update(SpecialStatEffect).where(SpecialStatEffect.effect_id == effect_id).values(**updates).returning(SpecialStatEffect) # <--- ИЗМЕНЕНО
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        updated_effect = result.scalars().first()
        if updated_effect:
            await self.db_session.flush() # <--- ИЗМЕНЕНО
            logger.info(f"Эффект (ID: {effect_id}) обновлен в сессии.")
            return updated_effect
        else:
            logger.warning(f"Эффект с ID {effect_id} не найден для обновления.")
            return None

    async def delete_effect(self, effect_id: int) -> bool: # <--- ИЗМЕНЕНО
        """Удаляет эффект по его ID."""
        stmt = delete(SpecialStatEffect).where(SpecialStatEffect.effect_id == effect_id) # <--- ИЗМЕНЕНО
        result = await self.db_session.execute(stmt) # <--- ИЗМЕНЕНО
        if result.rowcount > 0:
            await self.db_session.flush() # <--- ИЗМЕНЕНО
            logger.info(f"Эффект (ID: {effect_id}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Эффект с ID {effect_id} не найден для удаления.")
            return False