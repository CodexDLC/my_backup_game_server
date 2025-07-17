# game_server/app_discord_bot/app/services/admin/game_server_layout_service.py

from typing import Dict, Any, List, Optional
import discord
import uuid
import copy
import logging
import inject

from game_server.app_discord_bot.app.constant.constants_world import DEFAULT_ALLOW_BUTTON_INTERACTION_PERMISSIONS, DEFAULT_DENY_PERMISSIONS
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations

from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
# ▼▼▼ ДОБАВЛЕНЫ ИМПОРТЫ ДЛЯ РАБОТЫ С РОЛЯМИ ▼▼▼
from game_server.app_discord_bot.app.constant.roles_blueprint import ONLINE_ROLE, OFFLINE_ROLE
from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntitySyncRequest
from game_server.contracts.dtos.shard.commands import SaveShardCommandDTO
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload



class GameServerLayoutService:
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client,
        base_ops: BaseDiscordOperations,
        request_helper: RequestHelper,
        guild_config_manager: GuildConfigManager,
        cache_sync_manager: CacheSyncManager,
        logger: logging.Logger,
    ):
        self.bot = bot
        self.base_ops = base_ops
        self.channels_config = CHANNELS_CONFIG
        self.request_helper = request_helper
        self.guild_config_manager = guild_config_manager
        self.cache_sync_manager = cache_sync_manager
        self.logger = logger
        self.permissions_sets = self.channels_config.get("permissions_sets", {})
        self.ROLE_PERMISSION_MAP = {
            "admin_only": "Admin",
            "moderator_only": "Moderator"
        }

    async def setup_game_server_layout(self, guild_id: int, roles: Dict[str, discord.Role]) -> Dict[str, Any]:
        """
        Разворачивает структуру игрового шарда в Discord.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild: raise ValueError(f"Discord server with ID {guild_id} not found.")

        game_layout_config = self.channels_config.get("game_server_layout")
        if not game_layout_config: raise ValueError("Конфигурация 'game_server_layout' не найдена.")

        self.logger.info(f"Начало развертывания Game Server Layout для гильдии {guild_id}.")
        entities_to_sync: List[Dict[str, Any]] = []
        created_categories: Dict[str, discord.CategoryChannel] = {}
        welcome_channel_id: Optional[int] = None
        player_channel_category_ids_map: Dict[str, int] = {}
        cached_layout_for_redis: Dict[str, Any] = {"categories": {}, "player_channel_categories": {}}

        # ИЗМЕНЕНИЕ: Добавляем параметр `channel_name`
        def _prepare_overwrites(permissions_key: str, channel_name: Optional[str] = None) -> Dict[discord.Role, discord.PermissionOverwrite]:
            overwrites = {}
            everyone_role = guild.default_role
            online_role = roles.get(ONLINE_ROLE) # Получаем объект роли "Online player status"
            
            # СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ КАНАЛА "ПРИЁМНАЯ"
            if channel_name == "reception":
                # Используем предопределенный набор разрешений для @everyone
                overwrites[everyone_role] = discord.PermissionOverwrite(**DEFAULT_ALLOW_BUTTON_INTERACTION_PERMISSIONS)
                
                # Роль Online player status: Просмотр = ЗАПРЕТИТЬ
                if online_role:
                    overwrites[online_role] = discord.PermissionOverwrite(view_channel=False)
                else:
                    self.logger.warning(f"Роль '{ONLINE_ROLE}' не найдена. Канал 'приёмная' может быть виден онлайн-игрокам.")
                
                # Offline player status наследует от @everyone, поэтому для нее можно ничего специально не настраивать, она и так будет видеть канал.
                return overwrites

            # СУЩЕСТВУЮЩАЯ ЛОГИКА ДЛЯ ДРУГИХ КАНАЛОВ
            permission_values = self.permissions_sets.get(permissions_key, {})
            
            role_name_for_key = self.ROLE_PERMISSION_MAP.get(permissions_key)
            if role_name_for_key:
                target_role = roles.get(role_name_for_key)
                if target_role:
                    # Устанавливаем view_channel=False для @everyone по умолчанию для приватных каналов
                    overwrites[everyone_role] = discord.PermissionOverwrite(**DEFAULT_DENY_PERMISSIONS) # Или явно view_channel=False
                    overwrites[target_role] = discord.PermissionOverwrite(**permission_values)
                else:
                    self.logger.warning(f"Роль '{role_name_for_key}' не найдена. Канал будет полностью приватным.")
                    overwrites[everyone_role] = discord.PermissionOverwrite(**DEFAULT_DENY_PERMISSIONS) # Явно скрываем
            else:
                overwrites[everyone_role] = discord.PermissionOverwrite(**permission_values)
            
            return overwrites
        # Шаг 1: Создание категорий
        all_categories_config = list(game_layout_config.items()) + [
            (cat_info['name'], cat_info) for cat_info in game_layout_config.get("player_channel_categories", [])
        ]

        for key, value in all_categories_config:
            if isinstance(value, dict) and value.get('type') == 'category':
                try:
                    permissions_key = value.get('permissions')
                    # ИЗМЕНЕНИЕ: Для категории передаем None в channel_name
                    category_overwrites = _prepare_overwrites(permissions_key, channel_name=None) 

                    category = await self.base_ops.create_discord_category(guild, key, overwrites=category_overwrites)
                    created_categories[key] = category
                    
                    # ... остальная логика кэширования и синхронизации ...
                    is_player_category = any(d.get('name') == key for d in game_layout_config.get("player_channel_categories", []))
                    if is_player_category:
                        player_channel_category_ids_map[key] = category.id
                        cached_layout_for_redis["player_channel_categories"][key] = {"discord_id": category.id, "name": category.name, "channels": {}}
                    else:
                        cached_layout_for_redis["categories"][key] = {"discord_id": category.id, "name": category.name, "channels": {}}

                    entities_to_sync.append({"discord_id": category.id, "entity_type": "category", "name": category.name, "permissions": permissions_key, "description": value.get('description'), "guild_id": guild_id})
                except Exception as e:
                    self.logger.error(f"Ошибка при создании категории '{key}': {e}", exc_info=True)
                    raise

        # Шаг 2: Создание каналов внутри категорий
        for cat_name, parent_cat_obj in created_categories.items():
            # ... логика поиска channels_info остается такой же ...
            cat_data_original_for_channels = game_layout_config.get(cat_name)
            if not cat_data_original_for_channels:
                for pc_cat_item in game_layout_config.get("player_channel_categories", []):
                    if isinstance(pc_cat_item, dict) and pc_cat_item.get('name') == cat_name:
                        cat_data_original_for_channels = pc_cat_item
                        break

            if not cat_data_original_for_channels or "channels" not in cat_data_original_for_channels:
                continue
            
            for chan_name, chan_info in cat_data_original_for_channels.get("channels", {}).items():
                try:
                    permissions_key = chan_info.get('permissions')
                    # ИЗМЕНЕНИЕ: Передаем chan_name в _prepare_overwrites
                    channel_overwrites = _prepare_overwrites(permissions_key, channel_name=chan_name) 
                    
                    channel_type_str = chan_info.get('type', 'text')
                    channel = await self.base_ops.create_discord_channel(
                        guild, chan_name, channel_type_str,
                        parent_category=parent_cat_obj,
                        overwrites=channel_overwrites,
                        description=chan_info.get('description')
                    )
                    
                    if channel:
                        # ... остальная логика кэширования и синхронизации ...
                        entity_type = 'voice_channel' if channel_type_str == 'voice' else 'text_channel'
                        if chan_name == "приёмная": welcome_channel_id = channel.id
                        
                        target_dict_key = "player_channel_categories" if cat_name in cached_layout_for_redis["player_channel_categories"] else "categories"
                        cached_layout_for_redis[target_dict_key][cat_name]["channels"][chan_name] = {"discord_id": channel.id, "name": channel.name, "parent_id": parent_cat_obj.id}
                        
                        entities_to_sync.append({"discord_id": channel.id, "entity_type": entity_type, "name": channel.name, "description": chan_info.get('description'), "parent_id": parent_cat_obj.id, "permissions": permissions_key, "guild_id": guild_id})
                except Exception as e:
                    self.logger.error(f"Ошибка при создании канала '{chan_name}': {e}", exc_info=True)
                    raise
        
        # Шаг 3: Синхронизация сущностей Discord с бэкендом
        if not entities_to_sync:
            self.logger.warning("Не было создано ни одной сущности Discord для синхронизации.")
            return {"status": "success", "message": "Нет сущностей Discord для синхронизации, регистрация шарда отменена."}

        self.logger.info(f"Отправка {len(entities_to_sync)} сущностей Discord на бэкенд для синхронизации...")

        discord_sync_context = {
            "user_id": self.bot.user.id,
            "guild_id": guild_id,
            "channel_id": None,
            "command_source": "setup_game_server_layout_sync_entities"
        }

        discord_sync_request_payload = UnifiedEntitySyncRequest(
            guild_id=guild_id,
            entities_data=entities_to_sync
        )

        try:
            raw_ws_dict, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_entities,
                request_payload=discord_sync_request_payload,
                correlation_id=discord_sync_request_payload.correlation_id,
                discord_context=discord_sync_context
            )

            full_message = WebSocketMessage(**raw_ws_dict)
            response_payload = WebSocketResponsePayload(**full_message.payload)

            if response_payload.status == ResponseStatus.SUCCESS:
                self.logger.success("Синхронизация Discord сущностей успешно завершена.")
            else:
                error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при синхронизации Discord сущностей."
                raise RuntimeError(error_msg)
        except Exception as e:
            self.logger.error(f"Критическая ошибка при вызове API синхронизации Discord сущностей: {e}", exc_info=True)
            raise RuntimeError(f"Критическая ошибка при синхронизации Discord сущностей: {e}")


        # Шаг 4: Регистрация (сохранение) шарда на бэкенде
        self.logger.info(f"Регистрация игрового шарда {guild.name} (ID: {guild_id}) на бэкенде...")

        shard_register_context = {
            "user_id": self.bot.user.id,
            "guild_id": guild_id,
            "channel_id": None,
            "command_source": "setup_game_server_layout_register_shard"
        }

        shard_register_payload = SaveShardCommandDTO(
            discord_guild_id=guild_id,
            shard_name=guild.name,
            max_players=200,
            is_system_active=True
        )

        # 🔥 ИЗМЕНЕНИЕ ОТСТУПА: Этот try...except блок должен быть на одном уровне с self.logger.info выше
        try: 
            raw_ws_dict, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.shard.register,
                request_payload=shard_register_payload,
                correlation_id=shard_register_payload.correlation_id,
                discord_context=shard_register_context
            )

            full_message = WebSocketMessage(**raw_ws_dict)
            response_payload = WebSocketResponsePayload(**full_message.payload)

            if response_payload.status == ResponseStatus.SUCCESS:
                self.logger.success(f"Игровой шард {guild.name} (ID: {guild_id}) успешно зарегистрирован на бэкенде.")

                # ШАГ 5: КЭШИРОВАНИЕ КОНФИГУРАЦИИ ЛЕЙАУТА В REDIS (ИЗМЕНЕННАЯ ЛОГИКА)
                try:
                    if cached_layout_for_redis["categories"] or cached_layout_for_redis["player_channel_categories"]:

                        layout_data_to_cache = {
                            "welcome_channel_id": welcome_channel_id,
                            "player_channel_category_map": player_channel_category_ids_map,
                            "layout_structure": cached_layout_for_redis
                        }

                        await self.guild_config_manager.set_field(
                            guild_id=guild_id,
                            shard_type="game",
                            field_name=RedisKeys.FIELD_LAYOUT_CONFIG,
                            data=layout_data_to_cache
                        )
                        self.logger.success(f"Поле '{RedisKeys.FIELD_LAYOUT_CONFIG}' для гильдии {guild_id} сохранено в кэше.")

                        if roles:
                            roles_to_cache = {}
                            for role_name, role_obj in roles.items():
                                if role_obj:
                                    roles_to_cache[role_name] = {
                                        "discord_id": role_obj.id,
                                        "name": role_obj.name,
                                        "color": role_obj.color.value if isinstance(role_obj.color, discord.Color) else 0
                                    }
                                else:
                                    self.logger.warning(f"Объект роли '{role_name}' равен None, пропущено кэширование.")

                            if roles_to_cache:
                                await self.guild_config_manager.set_field(
                                    guild_id=guild_id,
                                    shard_type="game",
                                    field_name=RedisKeys.FIELD_SYSTEM_ROLES,
                                    data=roles_to_cache
                                )
                                self.logger.success(f"Поле '{RedisKeys.FIELD_SYSTEM_ROLES}' для гильдии {guild_id} сохранено в кэше.")
                            else:
                                self.logger.warning(f"Нет системных ролей для кэширования для гильдии {guild_id} (словарь ролей пуст после фильтрации).")
                        else:
                            self.logger.warning(f"Нет системных ролей для кэширования для гильдии {guild_id} (аргумент 'roles' пуст).")

                        self.logger.info(f"Запускаем синхронизацию полной конфигурации гильдии {guild_id} с бэкендом через CacheSyncManager...")
                        sync_success = await self.cache_sync_manager.sync_guild_config_to_backend(guild_id, shard_type="game")
                        if sync_success:
                            self.logger.success(f"Полная конфигурация гильдии {guild_id} успешно синхронизирована с бэкендом.")
                        else:
                            self.logger.error(f"Ошибка при синхронизации полной конфигурации гильдии {guild_id} с бэкендом.")

                    else:
                        self.logger.warning(f"Нет данных о лейауте для кэширования для гильдии {guild_id}.")

                except Exception as e:
                    self.logger.error(f"Не удалось закэшировать конфигурацию лейаута для гильдии {guild_id}: {e}", exc_info=True)

                return {
                    "status": "success", 
                    "message": "Развертывание и регистрация шарда завершены.", 
                    "details": response_payload.data,
                    "layout_config": layout_data_to_cache
                }
            else:
                error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при регистрации шарда."
                raise RuntimeError(error_msg)
        except Exception as e:
            self.logger.error(f"Критическая ошибка при вызове API регистрации шарда: {e}", exc_info=True)
            raise RuntimeError(f"Критическая ошибка при регистрации шарда: {e}")