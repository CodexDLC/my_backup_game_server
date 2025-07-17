# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/special_stat_effect_repository_impl.py

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

# Убедитесь, что путь к вашей модели SpecialStatEffect корректен
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ISpecialStatEffectRepository
from game_server.database.models.models import SpecialStatEffect

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class SpecialStatEffectRepositoryImpl(ISpecialStatEffectRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью SpecialStatEffect.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def get_effect_by_id(self, effect_id: int) -> Optional[SpecialStatEffect]:
        """Получает эффект по его ID в рамках переданной сессии."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.effect_id == effect_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_effect_by_keys(self, stat_key: str, affected_property: str, effect_type: str) -> Optional[SpecialStatEffect]:
        """Получает эффект по комбинации stat_key, affected_property и effect_type в рамках переданной сессии."""
        stmt = select(SpecialStatEffect).where(
            SpecialStatEffect.stat_key == stat_key,
            SpecialStatEffect.affected_property == affected_property,
            SpecialStatEffect.effect_type == effect_type
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_effects_for_stat(self, stat_key: str) -> List[SpecialStatEffect]:
        """Возвращает все эффекты, связанные с конкретной характеристикой, в рамках переданной сессии."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.stat_key == stat_key)
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def get_effects_for_property(self, affected_property: str) -> List[SpecialStatEffect]:
        """Возвращает все эффекты, влияющие на конкретное свойство, в рамках переданной сессии."""
        stmt = select(SpecialStatEffect).where(SpecialStatEffect.affected_property == affected_property)
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def create_effect(self, effect_data: Dict[str, Any]) -> SpecialStatEffect:
        """Создает новый эффект в рамках переданной сессии."""
        new_effect = SpecialStatEffect(**effect_data)
        self.db_session.add(new_effect)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Эффект '{effect_data.get('stat_key', 'N/A')}' создан в сессии.")
        return new_effect

    async def update_effect(self, effect_id: int, updates: Dict[str, Any]) -> Optional[SpecialStatEffect]:
        """Обновляет существующий эффект в рамках переданной сессии."""
        stmt = update(SpecialStatEffect).where(SpecialStatEffect.effect_id == effect_id).values(**updates).returning(SpecialStatEffect)
        result = await self.db_session.execute(stmt)
        updated_effect = result.scalars().first()
        if updated_effect:
            await self.db_session.flush() # flush, но НЕ commit
            logger.info(f"Эффект (ID: {effect_id}) обновлен в сессии.")
            return updated_effect
        else:
            logger.warning(f"Эффект с ID {effect_id} не найден для обновления.")
            return None

    async def delete_effect(self, effect_id: int) -> bool:
        """Удаляет эффект по его ID в рамках переданной сессии."""
        stmt = delete(SpecialStatEffect).where(SpecialStatEffect.effect_id == effect_id)
        result = await self.db_session.execute(stmt)
        if result.rowcount > 0:
            await self.db_session.flush() # flush, но НЕ commit
            logger.info(f"Эффект (ID: {effect_id}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Эффект с ID {effect_id} не найден для удаления.")
            return False
