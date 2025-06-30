# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/discord/discord_entity_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # Добавлен SQLAlchemyError для более общего отката

# Импорт вашей модели DiscordEntity
from game_server.database.models.models import DiscordEntity

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class DiscordEntityRepositoryImpl(IDiscordEntityRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью DiscordEntity.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM.
    Каждый метод репозитория управляет своей собственной транзакцией.
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create_discord_entity(self, entity_data: Dict[str, Any]) -> DiscordEntity:
        async with await self._get_session() as session:
            new_entity = DiscordEntity(**entity_data)
            session.add(new_entity)
            try:
                await session.commit() # НОВОЕ: Фиксируем изменения
                await session.refresh(new_entity) # Обновляем объект после коммита, чтобы получить ID
                logger.info(f"Сущность Discord '{new_entity.name}' (ID: {new_entity.id if hasattr(new_entity, 'id') else 'N/A'}, Discord ID: {new_entity.discord_id}) успешно создана и сохранена.")
                return new_entity
            except IntegrityError as e:
                await session.rollback() # Откат, если ошибка целостности
                logger.error(f"Ошибка целостности при создании сущности Discord '{entity_data.get('name')}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при создании сущности Discord: {e.orig}")
            except SQLAlchemyError as e: # Ловим общие ошибки SQLAlchemy
                await session.rollback()
                logger.error(f"Ошибка SQLAlchemy при создании сущности Discord '{entity_data.get('name')}': {e}", exc_info=True)
                raise
            except Exception as e:
                await session.rollback() # Откат при любой другой ошибке
                logger.error(f"Непредвиденная ошибка при создании сущности Discord '{entity_data.get('name')}': {e}", exc_info=True)
                raise

    async def get_discord_entity_by_discord_id(self, guild_id: int, discord_id: int) -> Optional[DiscordEntity]:
        async with await self._get_session() as session:
            stmt = select(DiscordEntity).where(
                DiscordEntity.guild_id == guild_id,
                DiscordEntity.discord_id == discord_id
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_discord_entity_by_name_and_parent(self, guild_id: int, name: str, parent_id: Optional[int]) -> Optional[DiscordEntity]:
        async with await self._get_session() as session:
            stmt = select(DiscordEntity).where(
                DiscordEntity.guild_id == guild_id,
                DiscordEntity.name == name,
                DiscordEntity.parent_id == parent_id
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_discord_entities_by_guild_id(self, guild_id: int) -> List[DiscordEntity]:
        async with await self._get_session() as session:
            stmt = select(DiscordEntity).where(DiscordEntity.guild_id == guild_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_discord_entities_by_type(self, guild_id: int, entity_type: str) -> List[DiscordEntity]:
        async with await self._get_session() as session:
            stmt = select(DiscordEntity).where(
                DiscordEntity.guild_id == guild_id,
                DiscordEntity.entity_type == entity_type
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_discord_entity(self, entity_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]:
        async with await self._get_session() as session:
            stmt = update(DiscordEntity).where(DiscordEntity.id == entity_id).values(**updates).returning(DiscordEntity)
            result = await session.execute(stmt)
            try:
                await session.commit() # НОВОЕ: Фиксируем изменения
                return result.scalars().first()
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Ошибка SQLAlchemy при обновлении сущности Discord ID {entity_id}: {e}", exc_info=True)
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при обновлении сущности Discord ID {entity_id}: {e}", exc_info=True)
                raise

    async def update_discord_entity_by_discord_id(self, guild_id: int, discord_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]:
        async with await self._get_session() as session:
            stmt = update(DiscordEntity).where(
                DiscordEntity.guild_id == guild_id,
                DiscordEntity.discord_id == discord_id
            ).values(**updates).returning(DiscordEntity)
            result = await session.execute(stmt)
            try:
                await session.commit() # НОВОЕ: Фиксируем изменения
                return result.scalars().first()
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Ошибка SQLAlchemy при обновлении сущности Discord ID {discord_id}: {e}", exc_info=True)
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при обновлении сущности Discord ID {discord_id}: {e}", exc_info=True)
                raise

    async def delete_discord_entity_by_id(self, entity_id: int) -> bool:
        async with await self._get_session() as session:
            stmt = delete(DiscordEntity).where(DiscordEntity.discord_id == entity_id)
            result = await session.execute(stmt)
            try:
                await session.commit() # НОВОЕ: Фиксируем изменения
                if result.rowcount > 0:
                    logger.info(f"Сущность Discord (ID: {entity_id}) успешно удалена.")
                    return True
                else:
                    logger.warning(f"Сущность Discord (ID: {entity_id}) не найдена для удаления.")
                    return False
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Ошибка SQLAlchemy при удалении сущности Discord ID {entity_id}: {e}", exc_info=True)
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при удалении сущности Discord ID {entity_id}: {e}", exc_info=True)
                raise

    async def delete_discord_entities_batch(self, guild_id: int, discord_ids: List[int]) -> int:
        async with await self._get_session() as session:
            if not discord_ids:
                return 0
            stmt = delete(DiscordEntity).where(
                DiscordEntity.guild_id == guild_id,
                DiscordEntity.discord_id.in_(discord_ids)
            )
            result = await session.execute(stmt)
            try:
                await session.commit() # НОВОЕ: Фиксируем изменения
                logger.info(f"Удалено {result.rowcount} сущностей Discord (Discord IDs: {discord_ids}) из БД.")
                return result.rowcount
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Ошибка SQLAlchemy при массовом удалении сущностей Discord для гильдии {guild_id}: {e}", exc_info=True)
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при массовом удалении сущностей Discord для гильдии {guild_id}: {e}", exc_info=True)
                raise

    async def get_total_entities_count(self, guild_id: Optional[int] = None) -> int:
        async with await self._get_session() as session:
            stmt = select(func.count(DiscordEntity.id))
            if guild_id:
                stmt = stmt.where(DiscordEntity.guild_id == guild_id)
            result = await session.execute(stmt)
            return result.scalar_one()
