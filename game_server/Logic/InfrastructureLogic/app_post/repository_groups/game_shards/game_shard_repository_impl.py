# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/game_shards/game_shard_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker # Импортируем async_sessionmaker (для инициализации фабрики)
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert


from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from game_server.database.models.models import GameShard 

from game_server.config.logging.logging_setup import app_logger as logger


class GameShardRepositoryImpl(IGameShardRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью GameShard.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM.
    """
    def __init__(self, db_session_factory: Type[AsyncSession]): # Теперь конструктор принимает фабрику сессий
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()
        
    async def create_shard(
        self,
        shard_name: str,
        discord_guild_id: int,
        max_players: int,
        is_admin_enabled: bool = False,
        is_system_active: bool = False
    ) -> GameShard:
        """
        Создает новую запись шарда в базе данных.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            new_shard = GameShard(
                shard_name=shard_name,
                discord_guild_id=discord_guild_id,
                max_players=max_players,
                is_admin_enabled=is_admin_enabled,
                is_system_active=is_system_active
            )
            session.add(new_shard)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Шард '{new_shard.shard_name}' (Guild ID: {new_shard.discord_guild_id}) создан.")
                return new_shard
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании шарда '{shard_name}': {e.orig}", exc_info=True)
                raise ValueError(f"Шард с таким именем или ID гильдии уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании шарда '{shard_name}': {e}", exc_info=True)
                raise

    async def upsert_shard(self, shard_data: Dict[str, Any]) -> GameShard:
        """
        Создает или обновляет запись шарда в базе данных.
        Использует discord_guild_id как ключ для определения конфликта.
        """
        discord_guild_id = shard_data.get("discord_guild_id")
        if not discord_guild_id:
            raise ValueError("discord_guild_id must be provided for upsert_shard operation.")

        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            try:
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

                result = await session.execute(upsert_stmt) # 🔥 ИЗМЕНЕНИЕ: session.execute
                upserted_shard = result.scalar_one_or_none()
                
                if not upserted_shard:
                    await session.rollback()
                    raise RuntimeError(f"UPSERT GameShard для Guild ID {discord_guild_id} не вернул объект.")

                await session.commit()
                logger.info(f"GameShard '{upserted_shard.shard_name}' (ID: {upserted_shard.discord_guild_id}) успешно добавлен/обновлен.")
                return upserted_shard

            except IntegrityError as e:
                await session.rollback() # 🔥 ИЗМЕНЕНИЕ: session.rollback
                logger.error(f"Ошибка целостности при UPSERT GameShard '{discord_guild_id}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении GameShard: {e.orig}")
            except Exception as e:
                await session.rollback() # 🔥 ИЗМЕНЕНИЕ: session.rollback
                logger.error(f"Непредвиденная ошибка при UPSERT GameShard '{discord_guild_id}': {e}", exc_info=True)
                raise


    async def get_shard_by_guild_id(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Получает шард по его Discord Guild ID.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = select(GameShard).where(GameShard.discord_guild_id == discord_guild_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_shard_by_name(self, shard_name: str) -> Optional[GameShard]:
        """
        Получает шард по его имени.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = select(GameShard).where(GameShard.shard_name == shard_name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all_shards(self) -> List[GameShard]:
        """
        Получает все записи шардов.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = select(GameShard)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_active_available_shards(self, max_players_from_settings: int) -> List[GameShard]:
        """
        Получает список активных и доступных шардов, которые могут принимать новых игроков.
        max_players_from_settings - общий лимит игроков, полученный из настроек.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = select(GameShard).where(
                GameShard.is_admin_enabled == True,
                GameShard.is_system_active == True,
                GameShard.current_players < max_players_from_settings
            ).order_by(GameShard.current_players.asc())
            result = await session.execute(stmt)
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
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = update(GameShard).where(GameShard.id == shard_id).values(**updates).returning(GameShard)
            result = await session.execute(stmt)
            await session.commit()
            logger.info(f"Шард (ID: {shard_id}) обновлен.")
            return result.scalars().first()

    async def increment_current_players(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Атомарно инкрементирует счетчик current_players для заданного шарда.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
                current_players=GameShard.current_players + 1
            ).returning(GameShard)
            result = await session.execute(stmt)
            await session.commit()
            logger.info(f"Счетчик игроков для шарда {discord_guild_id} увеличен.")
            return result.scalars().first()

    async def decrement_current_players(self, discord_guild_id: int) -> Optional[GameShard]:
        """
        Атомарно декрементирует счетчик current_players для заданного шарда.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
                current_players=GameShard.current_players - 1
            ).returning(GameShard)
            result = await session.execute(stmt)
            await session.commit()
            logger.info(f"Счетчик игроков для шарда {discord_guild_id} уменьшен.")
            return result.scalars().first()

    async def update_current_players_sync(self, discord_guild_id: int, actual_count: int) -> Optional[GameShard]:
        """
        Обновляет счетчик current_players для заданного шарда до фактического значения.
        Используется для ежесуточной синхронизации.
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = update(GameShard).where(GameShard.discord_guild_id == discord_guild_id).values(
                current_players=actual_count
            ).returning(GameShard)
            result = await session.execute(stmt)
            await session.commit()
            logger.info(f"Счетчик игроков для шарда {discord_guild_id} синхронизирован до {actual_count}.")
            return result.scalars().first()

    async def delete_shard(self, shard_id: int) -> bool:
        """
        Удаляет запись шарда по внутреннему ID.
        Использовать осторожно!
        """
        async with await self._get_session() as session: # 🔥 ИЗМЕНЕНИЕ: Используем сессию
            stmt = delete(GameShard).where(GameShard.id == shard_id)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.commit()
                logger.info(f"Шард (ID: {shard_id}) удален.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Шард (ID: {shard_id}) не найден для удаления.")
                return False
