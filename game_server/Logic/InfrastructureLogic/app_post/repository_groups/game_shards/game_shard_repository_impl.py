# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/game_shards/game_shard_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert as pg_insert


from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from game_server.database.models.models import GameShard

from game_server.config.logging.logging_setup import app_logger as logger


class GameShardRepositoryImpl(IGameShardRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью GameShard.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_shard(
        self,
        shard_name: str,
        discord_guild_id: int,
        max_players: int,
        is_admin_enabled: bool = False,
        is_system_active: bool = False
    ) -> GameShard:
        """
        Создает новую запись шарда в рамках переданной сессии.
        """
        new_shard = GameShard(
            shard_name=shard_name,
            discord_guild_id=discord_guild_id,
            max_players=max_players,
            is_admin_enabled=is_admin_enabled,
            is_system_active=is_system_active
        )
        self._session.add(new_shard)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Шард '{new_shard.shard_name}' (Guild ID: {new_shard.discord_guild_id}) добавлен в сессию.")
        return new_shard

    async def upsert_shard(self, shard_data: Dict[str, Any]) -> GameShard:
        """
        Создает или обновляет запись шарда в рамках переданной сессии.
        """
        discord_guild_id = shard_data.get("discord_guild_id")
        if not discord_guild_id:
            raise ValueError("discord_guild_id must be provided for upsert_shard operation.")

        updatable_fields = [
            "shard_name",
            "max_players",
            "is_system_active",
            "is_admin_enabled",
            "current_players"
        ]

        values_to_insert = {k: v for k, v in shard_data.items() if k not in ["id", "created_at", "updated_at"]}

        if "discord_guild_id" not in values_to_insert:
            values_to_insert["discord_guild_id"] = discord_guild_id

        insert_stmt = pg_insert(GameShard).values(**values_to_insert)

        set_clause = {}
        for field in updatable_fields:
            if field in insert_stmt.excluded:
                set_clause[field] = getattr(insert_stmt.excluded, field)

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[GameShard.discord_guild_id],
            set_=set_clause
        ).returning(GameShard)

        result = await self._session.execute(upsert_stmt)
        upserted_shard = result.scalar_one_or_none()

        if not upserted_shard:
            # Если upsert не вернул объект, это может быть проблемой, но rollback будет выше
            raise RuntimeError(f"UPSERT GameShard для Guild ID {discord_guild_id} не вернул объект.")

        await self._session.flush() # flush, но НЕ commit
        logger.info(f"GameShard '{upserted_shard.shard_name}' (ID: {upserted_shard.discord_guild_id}) добавлен/обновлен в сессии.")
        return upserted_shard


    async def get_shard_by_guild_id(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Получает шард по его Discord Guild ID в рамках переданной сессии.
        """
        stmt = select(GameShard).where(GameShard.discord_guild_id == discord_guild_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_shard_by_name(self, shard_name: str) -> Optional[GameShard]:
        """
        Получает шард по его имени в рамках переданной сессии.
        """
        stmt = select(GameShard).where(GameShard.shard_name == shard_name)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_all_shards(self) -> List[GameShard]:
        """
        Получает все записи шардов в рамках переданной сессии.
        """
        stmt = select(GameShard)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active_shards(self) -> List[GameShard]:
        """
        Получает список ВСЕХ активных шардов (без учета текущего количества игроков) в рамках переданной сессии.
        """
        stmt = select(GameShard).where(
            GameShard.is_admin_enabled == True,
            GameShard.is_system_active == True,
        )
        result = await self._session.execute(stmt)
        shards = result.scalars().all()
        logger.debug(f"Найдено {len(shards)} всех активных шардов в сессии.")
        return list(shards)


    async def get_active_available_shards(self, max_players_from_settings: int) -> List[GameShard]:
        """
        Получает список активных и доступных шардов, которые могут принимать новых игроков, в рамках переданной сессии.
        """
        stmt = select(GameShard).where(
            GameShard.is_admin_enabled == True,
            GameShard.is_system_active == True,
            GameShard.current_players < max_players_from_settings
        ).order_by(GameShard.current_players.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_shard_state(
        self,
        shard_id: int,
        updates: Dict[str, Any]
    ) -> Optional[GameShard]:
        """
        Обновляет состояние шарда по его внутреннему ID в рамках переданной сессии.
        """
        stmt = update(GameShard).where(GameShard.id == shard_id).values(**updates).returning(GameShard)
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Шард (ID: {shard_id}) обновлен в сессии.")
        return result.scalars().first()

    async def increment_current_players(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Атомарно инкрементирует счетчик current_players для заданного шарда в рамках переданной сессии.
        """
        stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
            current_players=GameShard.current_players + 1
        ).returning(GameShard)
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} увеличен в сессии.")
        return result.scalars().first()

    async def decrement_current_players(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Атомарно декрементирует счетчик current_players для заданного шарда в рамках переданной сессии.
        """
        stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
            current_players=GameShard.current_players - 1
        ).returning(GameShard)
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} уменьшен в сессии.")
        return result.scalars().first()

    async def update_current_players_sync(self, discord_guild_id: int, actual_count: int) -> Optional[GameShard]:
        """
        Обновляет счетчик current_players для заданного шарда до фактического значения в рамках переданной сессии.
        """
        stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
            current_players=actual_count
        ).returning(GameShard)
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} синхронизирован до {actual_count} в сессии.")
        return result.scalars().first()

    async def delete_shard(self, shard_id: int) -> bool:
        """
        Удаляет запись шарда по внутреннему ID в рамках переданной сессии.
        """
        stmt = delete(GameShard).where(GameShard.id == shard_id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Шард (ID: {shard_id}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Шард (ID: {shard_id}) не найден для удаления.")
            return False
