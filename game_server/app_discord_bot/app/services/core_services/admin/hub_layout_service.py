# game_server/app_discord_bot/app/services/admin/hub_layout_service.py

from typing import Dict, Any, List
import discord
import uuid
from pydantic import ValidationError
import logging
import inject

# --- ВАШИ ИМПОРТЫ ---
from game_server.app_discord_bot.app.services.utils.message_sender_service import MessageSenderService
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG
from game_server.app_discord_bot.app.services.core_services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntitySyncRequest
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload

# --- ДОБАВЛЕН ТОЛЬКО ИМПОРТ ДЛЯ НОВОЙ ФУНКЦИИ ---
from .message_login import send_registration_message_to_channel


class HubLayoutService:
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client,
        base_ops: BaseDiscordOperations,
        request_helper: RequestHelper,
        guild_config_manager: GuildConfigManager,
        cache_sync_manager: CacheSyncManager,
        message_sender_service: MessageSenderService,
        logger: logging.Logger,
    ):
        self.bot = bot
        self.base_ops = base_ops
        self.message_sender_service = message_sender_service
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
        
    async def setup_hub_layout(self, guild_id: int, roles: Dict[str, discord.Role]) -> Dict[str, Any]:
        """
        Разворачивает структуру хаб-сервера.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild: raise ValueError(f"Discord server with ID {guild_id} not found.")

        hub_layout = self.channels_config.get("hub_layout")
        if not hub_layout: raise ValueError("Конфигурация 'hub_layout' не найдена.")

        self.logger.info(f"Начало развертывания Hub Layout для гильдии {guild_id}.")
        entities_to_sync: List[Dict[str, Any]] = []
        created_categories: Dict[str, discord.CategoryChannel] = {}
        cached_hub_layout_for_redis: Dict[str, Any] = {"categories": {}}

        def _prepare_overwrites(permissions_key: str) -> Dict[discord.Role, discord.PermissionOverwrite]:
            overwrites = {}
            everyone_role = guild.default_role
            permission_values = self.permissions_sets.get(permissions_key, {})

            role_name_for_key = self.ROLE_PERMISSION_MAP.get(permissions_key)
            if role_name_for_key:
                target_role = roles.get(role_name_for_key)
                if target_role:
                    overwrites[everyone_role] = discord.PermissionOverwrite(view_channel=False)
                    overwrites[target_role] = discord.PermissionOverwrite(**permission_values)
                else:
                    self.logger.warning(f"Роль '{role_name_for_key}' не найдена. Канал будет полностью приватным.")
                    overwrites[everyone_role] = discord.PermissionOverwrite(view_channel=False)
            else:
                overwrites[everyone_role] = discord.PermissionOverwrite(**permission_values)
            
            return overwrites

        # Шаг 1: Создаем категории
        for category_name, category_data in hub_layout.items():
            if not isinstance(category_data, dict) or category_data.get('type') != 'category': continue
            try:
                permissions_key = category_data.get('permissions')
                category_overwrites = _prepare_overwrites(permissions_key)
                
                category_channel = await self.base_ops.create_discord_category(guild, category_name, overwrites=category_overwrites)
                created_categories[category_name] = category_channel
                
                entities_to_sync.append({"discord_id": str(category_channel.id), "entity_type": "category", "name": category_channel.name, "description": category_data.get('description'), "permissions": permissions_key, "guild_id": str(guild_id)})
                cached_hub_layout_for_redis["categories"][category_name] = {"discord_id": str(category_channel.id), "name": category_channel.name, "channels": {}}
            except Exception as e:
                self.logger.error(f"Ошибка при создании категории '{category_name}': {e}", exc_info=True)
                raise

        # Шаг 2: Создаем каналы
        for category_name, category_data in hub_layout.items():
            if "channels" not in category_data: continue
            parent_category = created_categories.get(category_name)
            if not parent_category:
                self.logger.warning(f"Категория-родитель '{category_name}' не найдена, пропускаем дочерние каналы.")
                continue
            
            for channel_name, channel_info in category_data["channels"].items():
                try:
                    permissions_key = channel_info.get('permissions')
                    channel_overwrites = _prepare_overwrites(permissions_key)
                    
                    channel_type_str = channel_info.get('type', 'text')
                    channel_obj = await self.base_ops.create_discord_channel(
                        guild, channel_name, channel_type_str,
                        parent_category=parent_category, overwrites=channel_overwrites,
                        description=channel_info.get('description')
                    )
                    if channel_obj:
                        entity_type = 'forum' if channel_type_str == 'forum' else ('news' if channel_type_str == 'news' else 'text_channel')
                        entities_to_sync.append({"discord_id": str(channel_obj.id), "entity_type": entity_type, "name": channel_obj.name, "description": channel_info.get('description'), "parent_id": str(parent_category.id), "permissions": permissions_key, "guild_id": str(guild_id)})
                        cached_hub_layout_for_redis["categories"][category_name]["channels"][channel_name] = {"discord_id": str(channel_obj.id), "name": channel_obj.name, "parent_id": str(parent_category.id)}
                except Exception as e:
                    self.logger.error(f"Ошибка при создании канала '{channel_name}': {e}", exc_info=True)
                    raise
                    
        # Шаг 3: Отправка ВСЕХ собранных сущностей на бэкенд одним запросом
        if not entities_to_sync:
            self.logger.warning("Не было создано ни одной сущности для синхронизации.")
            return {"status": "success", "message": "Нет сущностей для синхронизации."}

        self.logger.info(f"Отправка {len(entities_to_sync)} сущностей на бэкенд для синхронизации...")
        
        discord_context = {
            "user_id": str(self.bot.user.id),
            "guild_id": str(guild_id),
            "command_source": "setup_hub_layout"
        }

        try:
            request_payload = UnifiedEntitySyncRequest(guild_id=str(guild_id), entities_data=entities_to_sync)

            self.logger.info("HubLayoutService: Pydantic-модель UnifiedEntitySyncRequest успешно создана.")

            raw_ws_dict, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_entities,
                request_payload=request_payload,
                correlation_id=request_payload.correlation_id,
                discord_context=discord_context
            )
            
            full_message = WebSocketMessage(**raw_ws_dict)
            response_payload = WebSocketResponsePayload(**full_message.payload)

            if response_payload.status == ResponseStatus.SUCCESS:
                self.logger.info("Синхронизация Hub Layout с бэкендом успешно завершена.")
                
                # # Шаг 4: Кэширование и синхронизация конфигурации
                # try:
                #     if cached_hub_layout_for_redis["categories"]:
                #         await self.guild_config_manager.set_field(
                #             guild_id=guild_id,
                #             shard_type="hub",
                #             field_name=RedisKeys.FIELD_LAYOUT_CONFIG,
                #             data=cached_hub_layout_for_redis
                #         )
                #         self.logger.success(f"Поле '{RedisKeys.FIELD_HUB_LAYOUT_CONFIG}' для гильдии {guild_id} сохранено в кэше.")

                #         sync_success_to_backend = await self.cache_sync_manager.sync_guild_config_to_backend(guild_id, shard_type="hub")
                #         if sync_success_to_backend:
                #             self.logger.success(f"Полная конфигурация гильдии {guild_id} успешно синхронизирована с бэкендом.")
                #         else:
                #             self.logger.error(f"Ошибка при синхронизации полной конфигурации гильдии {guild_id} с бэкендом.")
                #     else:
                #         self.logger.warning(f"Нет данных о Hub Layout для кэширования для гильдии {guild_id}.")
                # except Exception as e:
                #     self.logger.error(f"Не удалось закэшировать Hub Layout для гильдии {guild_id} или синхронизировать с бэкендом: {e}", exc_info=True)
                
                #
                # ▼▼▼ НАЧАЛО НОВОГО БЛОКА ▼▼▼
                #
                # Шаг 5: Отправка сообщения для регистрации
                try:
                    target_channel_key = "получить-доступ"
                    registration_channel_id = None
                    for category_data in cached_hub_layout_for_redis.get("categories", {}).values():
                        if target_channel_key in category_data.get("channels", {}):
                            registration_channel_id = category_data["channels"][target_channel_key]["discord_id"]
                            break
                    
                    if registration_channel_id:
                        self.logger.info(f"Отправка регистрационного сообщения в канал {registration_channel_id}...")
                        await send_registration_message_to_channel(
                            guild=guild,
                            registration_channel_id=int(registration_channel_id),
                            bot=self.bot,
                            message_sender_service=self.message_sender_service
                        )
                        self.logger.success("Регистрационное сообщение успешно отправлено.")
                    else:
                        self.logger.warning(f"Канал с ключом '{target_channel_key}' не найден. Сообщение не отправлено.")
                except Exception as e:
                    self.logger.error(f"Не удалось отправить регистрационное сообщение: {e}", exc_info=True)
                #
                # ▲▲▲ КОНЕЦ НОВОГО БЛОКА ▲▲▲
                #

                return {"status": "success", "message": response_payload.message, "details": response_payload.data}
            else:
                error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при синхронизации."
                raise RuntimeError(error_msg)
            
        except ValidationError as e:
            self.logger.error(f"HubLayoutService: Ошибка валидации Pydantic для UnifiedEntitySyncRequest: {e.errors()}", exc_info=True)
            raise RuntimeError(f"Ошибка валидации данных для синхронизации: {e.errors()}")
        except Exception as e:
            self.logger.error(f"Критическая ошибка при вызове API синхронизации: {e}", exc_info=True)
            raise RuntimeError("Критическая ошибка при вызове API синхронизации.")