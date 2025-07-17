# game_server/app_discord_bot/app/services/admin/role_management_service.py

from typing import Dict, Any, List, Optional
import discord
import logging
import inject


from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper

from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntitySyncRequest
from game_server.contracts.api_models.system.requests import GetAllStateEntitiesRequest
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload


class RoleManagementService:
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client,
        request_helper: RequestHelper,
        logger: logging.Logger,
        base_ops: BaseDiscordOperations,
        guild_config_manager: GuildConfigManager,
        cache_sync_manager: CacheSyncManager,
    ):
        self.bot = bot
        self.request_helper = request_helper
        self.logger = logger
        self.base_ops = base_ops
        self.guild_config_manager = guild_config_manager
        self.cache_sync_manager = cache_sync_manager
        self.logger.info("✨ RoleManagementService инициализирован.")

    async def sync_discord_roles(self, guild_id: int, shard_type: str, message: Optional[discord.Message] = None) -> Dict[str, discord.Role]:
        """
        Гарантирует наличие системных ролей в Discord и возвращает их.
        1. Получает список системных ролей из БД.
        2. Для каждой роли вызывает create_or_update_role, чтобы создать ее в Discord, если она отсутствует.
        3. Собирает созданные/найденные объекты ролей в словарь.
        4. Синхронизирует ID этих ролей с бэкендом.
        5. Возвращает словарь с объектами ролей для дальнейшего использования.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord server with ID {guild_id} not found.")

        if message:
            await message.edit(content="Этап 1/3: Получение системных ролей с бэкенда...")
        self.logger.info(f"Запрос системных ролей с бэкенда для гильдии {guild_id} (тип шарда: {shard_type})...")

        system_roles_from_backend = []
        try:
            get_entities_payload = GetAllStateEntitiesRequest(guild_id=guild_id, entity_type="role")
            raw_ws_dict, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.state_entity.get_all,
                request_payload=get_entities_payload,
                correlation_id=get_entities_payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "sync_roles_get_states", "shard_type": shard_type}
            )
            
            full_message = WebSocketMessage(**raw_ws_dict)
            response_payload = WebSocketResponsePayload(**full_message.payload)

            if response_payload.status != ResponseStatus.SUCCESS:
                error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при получении системных ролей."
                raise RuntimeError(error_msg)
            
            all_state_entities = response_payload.data.get("entities", [])
            system_roles_from_backend = [se for se in all_state_entities if se.get("ui_type") in ["access_level", "status_flag"]]
            self.logger.info(f"С бэкенда получено {len(system_roles_from_backend)} системных ролей для проверки.")
        except Exception as e:
            self.logger.error(f"Не удалось получить системные роли с бэкенда: {e}", exc_info=True)
            if message: await message.edit(content=f"Ошибка: Не удалось получить системные роли с бэкенда. {e}")
            raise

        if message: await message.edit(content=f"Этап 2/3: Создание {len(system_roles_from_backend)} системных ролей в Discord...")
        
        synced_roles: Dict[str, discord.Role] = {}
        entities_to_sync: List[Dict[str, Any]] = []

        for role_data in system_roles_from_backend:
            role_name = role_data.get("description")
            if not role_name:
                continue
            
            # Создаем или получаем роль в Discord
            role_obj = await self.base_ops.create_or_update_role(guild, role_name)
            synced_roles[role_name] = role_obj

            # Готовим данные для отправки на бэкенд
            entities_to_sync.append({
                "discord_id": role_obj.id,
                "entity_type": "role",
                "name": role_obj.name,
                "access_code": role_data.get("access_code"),
                "guild_id": guild_id
            })

        self.logger.info(f"Проверка и создание системных ролей в Discord завершены. Найдено/создано: {len(synced_roles)}.")
        if message: await message.edit(content=f"Этап 3/3: Синхронизация {len(entities_to_sync)} ролей с БД...")
        
        if not entities_to_sync:
            self.logger.warning("Нет системных ролей для синхронизации с бэкендом.")
            return {}

        sync_payload = UnifiedEntitySyncRequest(guild_id=guild_id, entities_data=entities_to_sync)
        try:
            raw_ws_dict, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_entities,
                request_payload=sync_payload,
                correlation_id=sync_payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "sync_roles_upsert", "shard_type": shard_type}
            )

            full_message = WebSocketMessage(**raw_ws_dict)
            response_payload = WebSocketResponsePayload(**full_message.payload)

            if response_payload.status != ResponseStatus.SUCCESS:
                error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при синхронизации ролей."
                raise RuntimeError(error_msg)
            
            self.logger.success("Синхронизация системных ролей с бэкендом успешно завершена.")
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при синхронизации системных ролей: {e}", exc_info=True)
            if message: await message.edit(content=f"Критическая ошибка при синхронизации ролей: {e}")
            raise
        
        # Возвращаем словарь с готовыми объектами ролей
        return synced_roles