# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/discord/discord_entity_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, delete, func

# Импорт вашей модели DiscordEntity
from game_server.database.models.models import DiscordEntity

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class DiscordEntityRepositoryImpl(IDiscordEntityRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью DiscordEntity.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_discord_entity(self, entity_data: Dict[str, Any]) -> DiscordEntity:
        new_entity = DiscordEntity(**entity_data)
        self._session.add(new_entity)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Сущность Discord '{new_entity.name}' (ID: {new_entity.id if hasattr(new_entity, 'id') else 'N/A'}, Discord ID: {new_entity.discord_id}) успешно добавлена в сессию.")
        return new_entity

    async def get_discord_entity_by_discord_id(self, guild_id: int, discord_id: int) -> Optional[DiscordEntity]:
        stmt = select(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.discord_id == discord_id
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_discord_entity_by_name_and_parent(self, guild_id: int, name: str, parent_id: Optional[int]) -> Optional[DiscordEntity]:
        stmt = select(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.name == name,
            DiscordEntity.parent_id == parent_id
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_discord_entities_by_guild_id(self, guild_id: int) -> List[DiscordEntity]:
        stmt = select(DiscordEntity).where(DiscordEntity.guild_id == guild_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_discord_entities_by_type(self, guild_id: int, entity_type: str) -> List[DiscordEntity]:
        stmt = select(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.entity_type == entity_type
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_discord_entity(self, entity_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]:
        stmt = update(DiscordEntity).where(DiscordEntity.id == entity_id).values(**updates).returning(DiscordEntity)
        result = await self._session.execute(stmt)
        updated_entity = result.scalars().first()
        if updated_entity:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Сущность Discord ID {entity_id} обновлена в сессии.")
        return updated_entity

    async def update_discord_entity_by_discord_id(self, guild_id: int, discord_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]:
        stmt = update(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.discord_id == discord_id
        ).values(**updates).returning(DiscordEntity)
        result = await self._session.execute(stmt)
        updated_entity = result.scalars().first()
        if updated_entity:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Сущность Discord ID {discord_id} обновлена в сессии.")
        return updated_entity

    async def delete_discord_entity_by_id(self, entity_id: int) -> bool:
        stmt = delete(DiscordEntity).where(DiscordEntity.discord_id == entity_id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Сущность Discord (ID: {entity_id}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Сущность Discord (ID: {entity_id}) не найдена для удаления.")
            return False

    async def delete_discord_entities_batch(self, guild_id: int, discord_ids: List[int]) -> int:
        if not discord_ids:
            return 0
        stmt = delete(DiscordEntity).where(
            DiscordEntity.guild_id == guild_id,
            DiscordEntity.discord_id.in_(discord_ids)
        )
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Удалено {result.rowcount} сущностей Discord (Discord IDs: {discord_ids}) из сессии.")
        return result.rowcount

    async def get_total_entities_count(self, guild_id: Optional[int] = None) -> int:
        stmt = select(func.count(DiscordEntity.id))
        if guild_id:
            stmt = stmt.where(DiscordEntity.guild_id == guild_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()
