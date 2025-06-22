# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/game_shards/game_shard_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.exc import IntegrityError, NoResultFound

# Импорт вашей модели GameShard
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from game_server.database.models.models import GameShard 

# Импорт интерфейса репозитория


# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # <-- ИМПОРТ ЛОГГЕРА


class GameShardRepositoryImpl(IGameShardRepository): # <-- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью GameShard.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM.
    """
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_shard(
        self,
        shard_name: str,
        discord_guild_id: int,
        max_players: int, # Max players будет приходить из universal settings
        is_admin_enabled: bool = False,
        is_system_active: bool = False
    ) -> GameShard:
        """
        Создает новую запись шарда в базе данных.
        """
        new_shard = GameShard(
            shard_name=shard_name,
            discord_guild_id=discord_guild_id,
            max_players=max_players,
            is_admin_enabled=is_admin_enabled,
            is_system_active=is_system_active
        )
        self.db_session.add(new_shard)
        try:
            await self.db_session.flush() # Используем flush
            # db_session.commit() не вызывается
            logger.info(f"Шард '{new_shard.shard_name}' (Guild ID: {new_shard.discord_guild_id}) добавлен в сессию.")
            return new_shard
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при создании шарда '{shard_name}': {e.orig}", exc_info=True)
            raise ValueError(f"Шард с таким именем или ID гильдии уже существует.")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Непредвиденная ошибка при создании шарда '{shard_name}': {e}", exc_info=True)
            raise

    async def get_shard_by_guild_id(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Получает шард по его Discord Guild ID.
        """
        stmt = select(GameShard).where(GameShard.discord_guild_id == discord_guild_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_shard_by_name(self, shard_name: str) -> Optional[GameShard]:
        """
        Получает шард по его имени.
        """
        stmt = select(GameShard).where(GameShard.shard_name == shard_name)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_all_shards(self) -> List[GameShard]:
        """
        Получает все записи шардов.
        """
        stmt = select(GameShard)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_available_shards(self, max_players_from_settings: int) -> List[GameShard]:
        """
        Получает список активных и доступных шардов, которые могут принимать новых игроков.
        max_players_from_settings - общий лимит игроков, полученный из настроек.
        """
        stmt = select(GameShard).where(
            GameShard.is_admin_enabled == True,
            GameShard.is_system_active == True,
            GameShard.current_players < max_players_from_settings
        ).order_by(GameShard.current_players.asc())
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def update_shard_state(
        self,
        shard_id: int,
        updates: Dict[str, Any]
    ) -> Optional[GameShard]:
        """
        Обновляет состояние шарда по его внутреннему ID.
        Поля для обновления могут включать is_admin_enabled, is_system_active, current_players, invite_link.
        """
        stmt = update(GameShard).where(GameShard.id == shard_id).values(**updates).returning(GameShard)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # Используем flush
        logger.info(f"Шард (ID: {shard_id}) обновлен в сессии.")
        return result.scalars().first()

    async def increment_current_players(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Атомарно инкрементирует счетчик current_players для заданного шарда.
        """
        stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
            current_players=GameShard.current_players + 1
        ).returning(GameShard)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # Используем flush
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} увеличен в сессии.")
        return result.scalars().first()

    async def decrement_current_players(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Атомарно декрементирует счетчик current_players для заданного шарда.
        """
        stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
            current_players=GameShard.current_players - 1
        ).returning(GameShard)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # Используем flush
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} уменьшен в сессии.")
        return result.scalars().first()

    async def update_current_players_sync(self, discord_guild_id: int, actual_count: int) -> Optional[GameShard]:
        """
        Обновляет счетчик current_players для заданного шарда до фактического значения.
        Используется для ежесуточной синхронизации.
        """
        stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
            current_players=actual_count
        ).returning(GameShard)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # Используем flush
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} синхронизирован до {actual_count} в сессии.")
        return result.scalars().first()

    async def delete_shard(self, shard_id: int) -> bool:
        """
        Удаляет запись шарда по внутреннему ID.
        Использовать осторожно!
        """
        stmt = delete(GameShard).where(GameShard.id == shard_id)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # Используем flush
        logger.info(f"Шард (ID: {shard_id}) помечен для удаления в сессии.")
        return result.rowcount > 0