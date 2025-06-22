# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/discord/discord_entity_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError # Исправлено: из sqlalchemy.exc

# Импорт вашей модели DiscordEntity
from game_server.database.models.models import DiscordEntity

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # <--- ИМПОРТ ЛОГГЕРА


class DiscordEntityRepositoryImpl(IDiscordEntityRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью DiscordEntity.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM.
    """
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_discord_entity(self, entity_data: Dict[str, Any]) -> DiscordEntity:
        """
        Создает новую сущность Discord в базе данных.
        entity_data должна содержать поля guild_id, entity_type, name, parent_id, permissions, description.
        """
        new_entity = DiscordEntity(**entity_data)
        self.db_session.add(new_entity)
        try:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: flush (вместо commit/refresh)
            logger.info(f"Сущность Discord '{new_entity.name}' (ID: {new_entity.id if hasattr(new_entity, 'id') else 'N/A'}, Discord ID: {new_entity.discord_id}) добавлена в сессию.")
            return new_entity
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при создании сущности Discord '{entity_data.get('name')}': {e.orig}", exc_info=True)
            raise ValueError(f"Ошибка целостности при создании сущности Discord: {e.orig}")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Непредвиденная ошибка при создании сущности Discord '{entity_data.get('name')}': {e}", exc_info=True)
            raise

    async def get_discord_entity_by_discord_id(self, guild_id: int, discord_id: int) -> Optional[DiscordEntity]:
        """
        Получает сущность Discord по её Discord ID и ID гильдии.
        """
        stmt = select(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.discord_id == discord_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_discord_entity_by_name_and_parent(self, guild_id: int, name: str, parent_id: Optional[int]) -> Optional[DiscordEntity]:
        """
        Получает сущность Discord по имени, ID гильдии и ID родительской категории.
        """
        stmt = select(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.name == name,
            DiscordEntity.parent_id == parent_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_discord_entities_by_guild_id(self, guild_id: int) -> List[DiscordEntity]:
        """
        Получает все сущности Discord для указанного ID гильдии.
        """
        stmt = select(DiscordEntity).where(DiscordEntity.guild_id == guild_id)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def update_discord_entity(self, entity_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]:
        """
        Обновляет сущность Discord по её внутреннему ID в базе данных.
        """
        stmt = update(DiscordEntity).where(DiscordEntity.id == entity_id).values(**updates).returning(DiscordEntity)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # <--- ИЗМЕНЕНО: flush (вместо commit)
        logger.info(f"Сущность Discord (ID: {entity_id}) обновлена в сессии.")
        return result.scalars().first()

    async def update_discord_entity_by_discord_id(self, guild_id: int, discord_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]:
        """
        Обновляет сущность Discord по её Discord ID и ID гильдии.
        """
        stmt = update(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.discord_id == discord_id
        ).values(**updates).returning(DiscordEntity)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # <--- ИЗМЕНЕНО: flush (вместо commit)
        logger.info(f"Сущность Discord (Discord ID: {discord_id}) обновлена в сессии.")
        return result.scalars().first()

    async def delete_discord_entity_by_id(self, entity_id: int) -> bool:
        """
        Удаляет сущность Discord по её внутреннему ID.
        """
        stmt = delete(DiscordEntity).where(DiscordEntity.id == entity_id)
        result = await self.db_session.execute(stmt)
        if result.rowcount > 0: # Проверяем, что что-то было удалено
            await self.db_session.flush() # <--- ИЗМЕНЕНО: flush (вместо commit)
            logger.info(f"Сущность Discord (ID: {entity_id}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Сущность Discord (ID: {entity_id}) не найдена для удаления.")
            return False

    async def delete_discord_entities_batch(self, guild_id: int, discord_ids: List[int]) -> int:
        """
        Удаляет пачку сущностей Discord по их Discord ID и ID гильдии.
        Возвращает количество удаленных записей.
        """
        if not discord_ids:
            return 0
        stmt = delete(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.discord_id.in_(discord_ids)
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # <--- ИЗМЕНЕНО: flush (вместо commit)
        logger.info(f"Удалено {result.rowcount} сущностей Discord (Discord IDs: {discord_ids}) в сессии.")
        return result.rowcount

    async def get_total_entities_count(self, guild_id: Optional[int] = None) -> int:
        """
        Получает общее количество сущностей, опционально для конкретной гильдии.
        """
        stmt = select(func.count(DiscordEntity.id))
        if guild_id:
            stmt = stmt.where(DiscordEntity.guild_id == guild_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one()