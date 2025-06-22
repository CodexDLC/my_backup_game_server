# game_server/Logic/ApplicationLogic/api_reg/ShardManagement/shard_management_logic.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты репозиториев


# --- ИМПОРТЫ ДЛЯ ЛОГИЧЕСКИХ МОДУЛЕЙ (БУДУЩИЕ ФАЙЛЫ) ---
# Например:
# from game_server.Logic.ApplicationLogic.api_reg.ShardManagement.shard_creation_service import create_new_shard_logic
# from game_server.Logic.ApplicationLogic.api_reg.ShardManagement.shard_selection_service import select_available_shard_logic
# from game_server.Logic.ApplicationLogic.api_reg.ShardManagement.shard_activation_service import activate_reserve_shard_logic
# ----------------------------------------------------

# Передаем CentralRedisClient в конструктор, так как он будет нужен для специализированных менеджеров

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.account_game_data_repository import AccountGameDataRepositoryImpl
# --- ИМПОРТ МЕНЕДЖЕРА REDIS-СЧЕТЧИКОВ ---
# from game_server.Logic.InfrastructureLogic.app_cache.services.shard_count_cache_manager import ShardCountCacheManager
# --------------------------------------


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class ShardManagementLogic:
    """
    Бизнес-логика (координатор/фасад) для управления игровыми шарадами (слоями) и распределением игроков.
    Предоставляет высокоуровневый API, вызывая специализированные логические функции из других модулей.
    """
    def __init__(self, db_session: AsyncSession, redis_client: CentralRedisClient):
        self.game_shard_repository = GameShardRepository(db_session)
        self.account_game_data_repository = AccountGameDataRepositoryImpl(db_session)
        self.redis_client = redis_client
        # --- ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА REDIS-СЧЕТЧИКОВ ---
        # self.shard_count_cache_manager = ShardCountCacheManager(redis_client=redis_client)
        # ----------------------------------------------------

    # --- 1. Метод для сохранения/обновления нового шарда (ВНЕШНИЙ) ---
    async def register_or_update_game_shard(
        self,
        discord_guild_id: int,
        shard_name: str,
        max_players_limit: int,
        shard_id: Optional[int] = None,
        is_admin_enabled: Optional[bool] = None,
        is_system_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Регистрирует новый Discord-сервер как шард или обновляет существующий.
        Делегирует логику создания/обновления специализированному сервису.
        """
        logger.info(f"Координация регистрации/обновления шарда Guild ID: {discord_guild_id}.")
        # --- ДЕЛЕГИРОВАНИЕ ЛОГИКИ В ОТДЕЛЬНЫЙ МОДУЛЬ/ФУНКЦИЮ ---
        # Здесь будет вызвана функция из другого файла, например:
        # return await shard_creation_service.handle_shard_registration(
        #     self.game_shard_repository,
        #     self.shard_count_cache_manager, # Возможно, потребуется для инициализации Redis счетчика
        #     discord_guild_id, shard_name, max_players_limit, shard_id, is_admin_enabled, is_system_active
        # )
        # Пока заглушка:
        # Ваш существующий код создания/обновления из прошлого ответа, пока не вынесено в отдельный модуль
        existing_shard = None
        if shard_id:
            existing_shard = await self.game_shard_repository.get_shard_by_id(shard_id)
        if not existing_shard:
            existing_shard = await self.game_shard_repository.get_shard_by_guild_id(discord_guild_id)

        if existing_shard:
            updates = {}
            if shard_name is not None and existing_shard.shard_name != shard_name: updates["shard_name"] = shard_name
            if max_players_limit is not None and existing_shard.max_players != max_players_limit: updates["max_players"] = max_players_limit
            if is_admin_enabled is not None and existing_shard.is_admin_enabled != is_admin_enabled: updates["is_admin_enabled"] = is_admin_enabled
            if is_system_active is not None and existing_shard.is_system_active != is_system_active: updates["is_system_active"] = is_system_active
            
            if updates:
                updated_shard = await self.game_shard_repository.update_shard_state(existing_shard.id, updates)
                logger.info(f"Шард '{updated_shard.shard_name}' (ID: {updated_shard.id}) обновлен.")
                return updated_shard.__dict__
            else:
                logger.info(f"Шард '{existing_shard.shard_name}' (ID: {existing_shard.id}) уже существует и не требует обновлений.")
                return existing_shard.__dict__
        else:
            new_shard = await self.game_shard_repository.create_shard(
                shard_name=shard_name, discord_guild_id=discord_guild_id, max_players=max_players_limit,
                is_admin_enabled=False, is_system_active=False
            )
            # await self.shard_count_cache_manager.set_shard_player_count(new_shard.discord_guild_id, 0)
            logger.info(f"Новый шард '{new_shard.shard_name}' успешно создан с ID {new_shard.id}.")
            return new_shard.__dict__

    # --- 2. Метод для сортировки и выбора шарда для игрока (ВНЕШНИЙ) ---
    async def assign_player_to_available_shard(
        self, account_id: int, global_max_players_limit: int
    ) -> Dict[str, Any]:
        """
        Главный метод, который выбирает подходящий шард для нового игрока,
        привязывает его и инкрементирует счетчик. Делегирует логику выбора и активации.
        """
        logger.info(f"Координация назначения игрока {account_id} на доступный шард.")
        # --- ДЕЛЕГИРОВАНИЕ ЛОГИКИ В ОТДЕЛЬНЫЙ МОДУЛЬ/ФУНКЦИЮ ---
        # Здесь будет вызвана функция из другого файла, например:
        # return await shard_selection_service.handle_player_assignment(
        #     self.game_shard_repository,
        #     self.account_game_data_repository,
        #     self.shard_count_cache_manager,
        #     account_id, global_max_players_limit,
        #     _activate_next_reserve_shard_logic # Передаем ссылку на функцию активации
        # )
        # Пока заглушка:
        raise NotImplementedError("Логика выбора шарда будет реализована в отдельном модуле.")

    # --- ВНУТРЕННИЙ ВСПОМОГАТЕЛЬНЫЙ МЕТОД (будет вынесен) ---
    async def _activate_next_reserve_shard(
        self, global_max_players_limit: int
    ) -> Optional[Dict[str, Any]]:
        """
        Внутренний метод для активации следующего резервного шарда.
        Будет вынесен в отдельный модуль логики активации.
        """
        # --- ДЕЛЕГИРОВАНИЕ ЛОГИКИ В ОТДЕЛЬНЫЙ МОДУЛЬ/ФУНКЦИЮ ---
        # return await shard_activation_service.activate_reserve_shard_logic(
        #     self.game_shard_repository,
        #     global_max_players_limit
        # )
        # Пока заглушка:
        raise NotImplementedError("Логика активации резервного шарда будет реализована в отдельном модуле.")

    # --- Админские/вспомогательные функции, которые останутся здесь или будут вынесены ---
    async def set_shard_admin_status(self, shard_id: int, is_enabled: bool) -> Optional[Dict[str, Any]]:
        # Ваш текущий код...
        logger.info(f"Попытка изменить статус is_admin_enabled для шарда ID {shard_id} на {is_enabled}.")
        try:
            updated_shard = await self.game_shard_repository.update_shard_state(
                shard_id=shard_id,
                updates={"is_admin_enabled": is_enabled}
            )
            if updated_shard: return updated_shard.__dict__
            else: return None
        except Exception as e: raise

    async def set_shard_system_active_status(self, shard_id: int, is_active: bool) -> Optional[Dict[str, Any]]:
        # Ваш текущий код...
        logger.info(f"Попытка изменить статус is_system_active для шарда ID {shard_id} на {is_active}.")
        try:
            updated_shard = await self.game_shard_repository.update_shard_state(
                shard_id=shard_id,
                updates={"is_system_active": is_active}
            )
            if updated_shard: return updated_shard.__dict__
            else: return None
        except Exception as e: raise

    async def get_all_shards_overview(self) -> List[Dict[str, Any]]:
        # Ваш текущий код...
        logger.info("Запрос информации обо всех шардах.")
        try:
            all_shards = await self.game_shard_repository.get_all_shards()
            overview_list = [shard.__dict__ for shard in all_shards]
            logger.info(f"Получено {len(overview_list)} шардов.")
            return overview_list
        except Exception as e: raise

    # --- Функции для очистки и синхронизации (будут реализованы позже) ---
    # async def cleanup_inactive_players(...)
    # async def recalculate_and_sync_all_shards_data(...)