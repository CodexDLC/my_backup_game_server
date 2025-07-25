# game_server/app_discord_bot/app/services/admin/discord_entity_service.py
import logging
import json # НОВОЕ: для парсинга JSON из Redis
from typing import Dict, Any, List, Optional
import discord
import uuid
import inject

from game_server.app_discord_bot.app.services.core_services.admin.article_management_service import ArticleManagementService
from game_server.app_discord_bot.app.services.core_services.admin.game_server_layout_service import GameServerLayoutService
from game_server.app_discord_bot.app.services.core_services.admin.hub_layout_service import HubLayoutService
from game_server.app_discord_bot.app.services.core_services.admin.message_login import send_login_message_to_reception_channel
from game_server.app_discord_bot.app.services.core_services.admin.role_management_service import RoleManagementService
from game_server.app_discord_bot.app.services.utils.name_formatter import NameFormatter
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.contracts.api_models.discord.entity_management_requests import GetDiscordEntitiesRequest, UnifiedEntityBatchDeleteRequest
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
from game_server.app_discord_bot.app.services.utils.message_sender_service import MessageSenderService


class DiscordEntityService:
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client,
        guild_config_manager: GuildConfigManager,
        request_helper: RequestHelper,
        name_formatter: NameFormatter,
        cache_sync_manager: CacheSyncManager,
        game_server_layout_service: GameServerLayoutService,
        hub_layout_service: HubLayoutService,
        role_management_service: RoleManagementService,
        article_management_service: ArticleManagementService,
        message_sender_service: MessageSenderService, 
        logger: logging.Logger,
    ):
        self.bot = bot
        self.logger = logger
        self.guild_config_manager = guild_config_manager
        self.request_helper = request_helper
        self.name_formatter = name_formatter
        self.cache_sync_manager = cache_sync_manager
        self.game_server_layout_service = game_server_layout_service
        self.hub_layout_service = hub_layout_service
        self.role_management_service = role_management_service
        self.article_management_service = article_management_service
        self.message_sender_service = message_sender_service
        self.logger.info("✨ DiscordEntityService инициализирован.")
        
    async def setup_game_server_layout(self, guild_id: int) -> Dict[str, Any]:
        # ... (метод setup_game_server_layout остается без изменений) ...
        """
        Выполняет полную последовательную настройку игрового сервера:
        1. Синхронизирует/создает роли.
        2. Создает лейаут каналов, используя созданные роли.
        3. Отправляет сообщение с кнопкой логина в канал 'reception'.
        """
        self.logger.info(f"Запуск полного цикла настройки для Game Server {guild_id}.")
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            self.logger.error(f"Гильдия с ID {guild_id} не найдена. Невозможно настроить игровой сервер.")
            return {"status": "failed", "message": f"Гильдия {guild_id} не найдена."}

        # Шаг 1: Создаем роли и получаем их объекты
        self.logger.info(f"Синхронизация Discord ролей для игрового сервера {guild_id}...")
        synced_roles = await self.role_management_service.sync_discord_roles(guild_id, "game")
        self.logger.success(f"Роли для игрового сервера {guild_id} синхронизированы.")

        # Шаг 2: Создаем лейаут каналов, передавая созданные роли
        self.logger.info(f"Создание лейаута каналов для игрового сервера {guild_id}...")
        layout_creation_result = await self.game_server_layout_service.setup_game_server_layout(guild_id, roles=synced_roles)
        
        if layout_creation_result.get("status") != "success":
            self.logger.error(f"Не удалось создать лейаут каналов для игрового сервера {guild_id}: {layout_creation_result.get('message')}")
            return layout_creation_result # Возвращаем результат ошибки создания лейаута

        self.logger.success(f"Лейаут каналов для игрового сервера {guild_id} успешно создан.")

        # 🔥 ИЗМЕНЕНИЕ: Шаг 3: Отправляем сообщение с кнопкой логина в канал 'reception'
        self.logger.info(f"Проверка наличия существующего сообщения логина в Redis для гильдии {guild_id}...")
        
        # Получаем login_message_id из Redis
        existing_login_message_id = await self.guild_config_manager.get_field(
            guild_id=guild_id,
            shard_type="game",
            field_name=RedisKeys.FIELD_LOGIN_MESSAGE_ID
        )

        if existing_login_message_id:
            self.logger.info(f"Сообщение логина уже существует (ID: {existing_login_message_id}) для гильдии {guild_id}. Новое сообщение не будет отправлено.")
        else:
            self.logger.info(f"Отправка сообщения логина в канал 'reception' для гильдии {guild_id}...")
            layout_config = layout_creation_result.get("layout_config") 

            if layout_config:
                # ▼▼▼ ИСПРАВЛЕНИЕ ЗДЕСЬ ▼▼▼
                # Передаем недостающие зависимости, которые уже есть в self
                sent_message = await send_login_message_to_reception_channel(
                    guild=guild,
                    layout_config=layout_config,
                    bot=self.bot,
                    message_sender_service=self.message_sender_service,
                    guild_config_manager=self.guild_config_manager
                )
                if sent_message:
                    self.logger.success(f"Сообщение логина успешно отправлено в канал 'reception' для гильдии {guild_id}.")
                else:
                    self.logger.error(f"Не удалось отправить сообщение логина в канал 'reception' для гильдии {guild_id}.")

        self.logger.success(f"Полный цикл настройки для Game Server {guild_id} завершен.")
        return {"status": "success", "message": f"Игровой сервер {guild_id} успешно настроен."}

    async def setup_hub_layout(self, guild_id: int) -> Dict[str, Any]:
        # ... (метод setup_hub_layout остается без изменений) ...
        """
        Выполняет полную последовательную настройку хаб-сервера.
        1. Синхронизирует/создает роли.
        2. Создает лейаут каналов, используя созданные роли.
        """
        self.logger.info(f"Запуск полного цикла настройки для Hub Server {guild_id}.")
        # Шаг 1: Создаем роли и получаем их объекты
        synced_roles = await self.role_management_service.sync_discord_roles(guild_id, "hub")
        # Шаг 2: Создаем лейаут, передавая созданные роли
        return await self.hub_layout_service.setup_hub_layout(guild_id, roles=synced_roles)

    async def teardown_discord_layout(self, guild_id: int, shard_type: str) -> Dict[str, Any]:
        """
        Удаляет все сущности Discord для гильдии.
        Сначала удаляет персональные каналы и роли игроков, затем общие структуры.
        После удаления очищает кэш.
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            self.logger.warning(f"Гильдия с ID {guild_id} не найдена для удаления лейаута.")
            return {"status": "skipped", "message": f"Гильдия {guild_id} не найдена."}

        self.logger.info(f"Начало полного удаления лейаута Discord для гильдии {guild_id} (тип: {shard_type}).")
        
        # =====================================================================
        # Шаг 1: Удаление персональных каналов и ролей игроков
        # =====================================================================
        self.logger.info(f"Поиск и удаление персональных каналов и ролей игроков для гильдии {guild_id} (тип: {shard_type})...")
        
        # Получаем список всех зарегистрированных Discord ID для данного шарда
        registered_player_ids_json = await self.guild_config_manager.get_field(
            guild_id=guild_id,
            shard_type=shard_type,
            field_name=RedisKeys.FIELD_REGISTERED_PLAYER_IDS
        )

        player_discord_ids: List[str] = []
        if registered_player_ids_json:
            try:
                # get_field уже декодирует JSON, поэтому тут просто проверка типа
                if isinstance(registered_player_ids_json, list):
                    player_discord_ids = [str(pid) for pid in registered_player_ids_json] # Приводим все к строкам
                else:
                    self.logger.warning(f"Поле '{RedisKeys.FIELD_REGISTERED_PLAYER_IDS}' для гильдии {guild_id} не является списком. Пропускаем удаление персональных данных.")
            except Exception as e:
                self.logger.error(f"Ошибка при парсинге списка игроков из Redis для гильдии {guild_id}: {e}", exc_info=True)
        
        if player_discord_ids:
            self.logger.info(f"Найдено {len(player_discord_ids)} зарегистрированных игроков для гильдии {guild_id}. Начинаем удаление их персональных сущностей.")
            for player_discord_id in player_discord_ids:
                try:
                    # Формируем ключ для данных аккаунта игрока
                    player_account_key = RedisKeys.PLAYER_ACCOUNT_DATA_HASH.format(
                        shard_id=guild_id, # Здесь guild_id используется как shard_id
                        discord_user_id=player_discord_id
                    )
                    
                    # Получаем все данные аккаунта игрока
                    # Если AccountDataManager предоставляет get_full_account_data_for_shard, то лучше использовать его
                    player_data_from_redis = await self.guild_config_manager.redis_client.hgetall(player_account_key)
                    
                    if player_data_from_redis:
                        discord_channels_str = player_data_from_redis.get(RedisKeys.FIELD_DISCORD_CHANNELS.encode('utf-8'))
                        discord_roles_str = player_data_from_redis.get(RedisKeys.FIELD_DISCORD_ROLES.encode('utf-8'))

                        # Удаление персональных каналов
                        if discord_channels_str:
                            try:
                                channel_ids = json.loads(discord_channels_str.decode('utf-8'))
                                for channel_id in channel_ids:
                                    try:
                                        channel = guild.get_channel(int(channel_id))
                                        if channel:
                                            await self.base_ops.delete_discord_channel(channel)
                                            self.logger.debug(f"Удален персональный канал {channel_id} для игрока {player_discord_id}.")
                                        else:
                                            self.logger.warning(f"Персональный канал {channel_id} игрока {player_discord_id} не найден на сервере, пропущен.")
                                    except Exception as e:
                                        self.logger.error(f"Ошибка при удалении персонального канала {channel_id} игрока {player_discord_id}: {e}", exc_info=True)
                            except (json.JSONDecodeError, TypeError) as e:
                                self.logger.error(f"Ошибка парсинга JSON для каналов игрока {player_discord_id}: {e}", exc_info=True)

                        # Удаление персональных ролей
                        if discord_roles_str:
                            try:
                                role_ids = json.loads(discord_roles_str.decode('utf-8'))
                                for role_id in role_ids:
                                    try:
                                        role = guild.get_role(int(role_id))
                                        if role:
                                            # base_ops.delete_discord_role должен быть реализован
                                            await self.role_management_service.delete_role(guild.id, role_id) # Используем role_management_service
                                            self.logger.debug(f"Удалена персональная роль {role_id} для игрока {player_discord_id}.")
                                        else:
                                            self.logger.warning(f"Персональная роль {role_id} игрока {player_discord_id} не найдена на сервере, пропущена.")
                                    except Exception as e:
                                        self.logger.error(f"Ошибка при удалении персональной роли {role_id} игрока {player_discord_id}: {e}", exc_info=True)
                            except (json.JSONDecodeError, TypeError) as e:
                                self.logger.error(f"Ошибка парсинга JSON для ролей игрока {player_discord_id}: {e}", exc_info=True)
                        
                        # Удаление хэша данных игрока из Redis
                        await self.guild_config_manager.redis_client.delete(player_account_key) # Предполагаем прямой доступ
                        self.logger.info(f"Удалены данные игрока {player_discord_id} из Redis (ключ: {player_account_key}).")
                    else:
                        self.logger.warning(f"Данные аккаунта игрока {player_discord_id} не найдены в Redis по ключу {player_account_key}. Пропущено.")

                except Exception as e:
                    self.logger.error(f"Общая ошибка при обработке игрока {player_discord_id} для удаления: {e}", exc_info=True)
            
            # После удаления всех персональных сущностей, удаляем сам список игроков из конфига шарда
            await self.guild_config_manager.delete_fields(
                guild_id=guild_id,
                shard_type=shard_type,
                fields=[RedisKeys.FIELD_REGISTERED_PLAYER_IDS]
            )
            self.logger.success(f"Список зарегистрированных игроков для гильдии {guild_id} удален из Redis.")
        else:
            self.logger.info(f"Список зарегистрированных игроков для гильдии {guild_id} пуст. Пропускаем удаление персональных сущностей.")


        entities_to_delete = []
        source = "Unknown"

        # Шаг 2 (бывший Шаг 1): Пытаемся получить данные общих сущностей из кэша (ПРЕДПОЧТИТЕЛЬНЫЙ ИСТОЧНИК)
        # Этот вызов get_all_fields должен теперь быть уверен, что FIELD_REGISTERED_PLAYER_IDS уже удален.
        # Если get_all_fields не исключает удаленные поля, это не проблема, т.к. нас интересуют layout и roles
        cached_config = await self.guild_config_manager.get_all_fields(guild_id, shard_type)

        if cached_config:
            self.logger.info(f"Данные общих сущностей для удаления получены из кэша Redis для гильдии {guild_id}.")
            source = "Redis Cache"
            
            # Этот блок Hub Layout должен быть вызван ТОЛЬКО если shard_type == "hub"
            # Текущая логика вызывается при любом shard_type, что некорректно
            if shard_type == "hub" and RedisKeys.FIELD_LAYOUT_CONFIG in cached_config:
                hub_layout_data = cached_config[RedisKeys.FIELD_LAYOUT_CONFIG]
                self.logger.debug(f"Парсинг Hub Layout из кэша.")
                for cat_name, cat_data in hub_layout_data.get('categories', {}).items():
                    entities_to_delete.append({'discord_id': cat_data['discord_id'], 'name': cat_name, 'entity_type': 'category'})
                    for chan_name, chan_data in cat_data.get('channels', {}).items():
                        entities_to_delete.append({'discord_id': chan_data['discord_id'], 'name': chan_name, 'entity_type': 'text_channel'})

            # Этот блок Game Server Layout должен быть вызван ТОЛЬКО если shard_type == "game"
            if shard_type == "game" and RedisKeys.FIELD_LAYOUT_CONFIG in cached_config:
                layout_data = cached_config[RedisKeys.FIELD_LAYOUT_CONFIG]
                self.logger.debug(f"Парсинг Game Server Layout из кэша.")
                for cat_type in ['categories', 'player_channel_categories']:
                    for cat_name, cat_data in layout_data.get('layout_structure', {}).get(cat_type, {}).items():
                        entities_to_delete.append({'discord_id': cat_data['discord_id'], 'name': cat_name, 'entity_type': 'category'})
                        for chan_name, chan_data in cat_data.get('channels', {}).items():
                            entities_to_delete.append({'discord_id': chan_data['discord_id'], 'name': chan_name, 'entity_type': 'text_channel'})
            
            if RedisKeys.FIELD_SYSTEM_ROLES in cached_config:
                self.logger.debug(f"Парсинг System Roles из кэша.")
                for role_name, role_data in cached_config[RedisKeys.FIELD_SYSTEM_ROLES].items():
                    entities_to_delete.append({'discord_id': role_data['discord_id'], 'name': role_name, 'entity_type': 'role'})

        # Шаг 3 (бывший Шаг 2): Если кэш пуст ИЛИ не удалось получить из него данные, ОБРАЩАЕМСЯ К БЭКЕНДУ (Fallback/Гарантия)
        if not entities_to_delete: 
            self.logger.warning(f"Локальный кэш для гильдии {guild_id} пуст или не содержит сущностей для удаления. Запрашиваем данные у бэкенда.")
            source = "Backend DB (Fallback)"
            try:
                get_entities_payload = GetDiscordEntitiesRequest(guild_id=guild_id)
                raw_ws_dict, _ = await self.request_helper.send_and_await_response(
                    api_method=self.request_helper.http_client_gateway.discord.get_entities,
                    request_payload=get_entities_payload,
                    correlation_id=get_entities_payload.correlation_id,
                    discord_context={"guild_id": guild_id, "command_source": "teardown_fallback"}
                )
                full_message = WebSocketMessage(**raw_ws_dict)
                response_payload = WebSocketResponsePayload(**full_message.payload)

                if response_payload.status != ResponseStatus.SUCCESS:
                    error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при получении списка сущностей."
                    raise RuntimeError(error_msg)
                
                retrieved_entities_from_backend = response_payload.data.get("entities", [])
                entities_to_delete.extend(retrieved_entities_from_backend)

            except Exception as e:
                self.logger.error(f"Критическая ошибка при получении данных от бэкенда для удаления: {e}", exc_info=True)
                return {"status": "failed", "message": f"Не удалось получить список сущностей для удаления: {e}"}

        # Если после всех попыток список сущностей все равно пуст
        if not entities_to_delete:
            self.logger.info(f"Не найдено сущностей для удаления для гильдии {guild_id} (проверены: {source}).")
            # После удаления персональных данных, если и общих нет, то просто удаляем конфиг и выходим.
            await self.guild_config_manager.delete_config(guild_id, shard_type) # Удаляем весь хэш конфига, включая поле players_ids, если оно осталось пустым
            self.logger.success(f"Конфигурация (Hash) для гильдии {guild_id} (ключ '{RedisKeys.GUILD_CONFIG_HASH.format(shard_type=shard_type, guild_id=guild_id)}') удалена из локального кэша.")
            return {"status": "skipped", "message": "Нет сущностей для удаления."}

        self.logger.info(f"Найдено {len(entities_to_delete)} общих сущностей для удаления (источник: {source}).")

        # # Шаг 4 (бывший Шаг 3): Сначала удаляем конфигурацию гильдии из бэкенд-Redis
        # self.logger.info(f"Инициируем удаление конфигурации гильдии {guild_id} из бэкенд-Redis через CacheSyncManager...")
        # delete_success_on_backend_redis = await self.cache_sync_manager.delete_guild_config_from_backend(guild_id, shard_type)
        
        # if not delete_success_on_backend_redis:
        #     self.logger.error(f"Не удалось удалить конфигурацию гильдии {guild_id} из бэкенд-Redis. Отменяем дальнейшее удаление.")
        #     return {"status": "failed", "message": "Не удалось удалить конфигурацию из бэкенд-Redis."}
        
        # self.logger.success(f"Конфигурация гильдии {guild_id} успешно удалена из бэкенд-Redis.")


        # Шаг 5 (бывший Шаг 4): Удаляем сущности из Discord (логика почти без изменений)
        discord_ids_to_delete = []
        for entity in filter(lambda e: e.get('entity_type') in ["text_channel", "voice_channel", "forum", "news"], entities_to_delete):
            try:
                channel = guild.get_channel(entity['discord_id'])
                if channel: await channel.delete()
                discord_ids_to_delete.append(entity['discord_id'])
            except discord.errors.NotFound:
                discord_ids_to_delete.append(entity['discord_id'])
            except Exception as e:
                self.logger.error(f"Ошибка при удалении канала {entity['name']}: {e}", exc_info=True)
        
        for entity in filter(lambda e: e.get('entity_type') == 'category', entities_to_delete):
            try:
                category = guild.get_channel(entity['discord_id'])
                if category: await category.delete()
                discord_ids_to_delete.append(entity['discord_id'])
            except discord.errors.NotFound:
                discord_ids_to_delete.append(entity['discord_id'])
            except Exception as e:
                self.logger.error(f"Ошибка при удалении категории {entity['name']}: {e}", exc_info=True)
        
        for entity in filter(lambda e: e.get('entity_type') == 'role', entities_to_delete):
            try:
                role = guild.get_role(entity['discord_id'])
                if role: await role.delete()
                discord_ids_to_delete.append(entity['discord_id'])
            except discord.errors.NotFound:
                discord_ids_to_delete.append(entity['discord_id'])
            except Exception as e:
                self.logger.error(f"Ошибка при удалении роли {entity['name']}: {e}", exc_info=True)

        # Шаг 6 (бывший Шаг 5): Отправляем запрос на массовое удаление сущностей Discord из БД
        if not discord_ids_to_delete:
            self.logger.info("Нет сущностей для удаления из БД (после попытки удаления из Discord).")
            return {"status": "success", "message": "Удаление не потребовалось."}
            
        delete_payload = UnifiedEntityBatchDeleteRequest(guild_id=guild_id, discord_ids=list(set(discord_ids_to_delete)))
        raw_ws_dict, _ = await self.request_helper.send_and_await_response(
            api_method=self.request_helper.http_client_gateway.discord.batch_delete_entities,
            request_payload=delete_payload,
            correlation_id=delete_payload.correlation_id,
            discord_context={"guild_id": guild_id, "command_source": "teardown_delete"}
        )
        full_message = WebSocketMessage(**raw_ws_dict)
        response_payload = WebSocketResponsePayload(**full_message.payload)

        if response_payload.status != ResponseStatus.SUCCESS:
            error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при массовом удалении сущностей."
            raise RuntimeError(error_msg)

        self.logger.success(f"Массовое удаление {len(discord_ids_to_delete)} сущностей из БД прошло успешно.")

        # Шаг 7 (бывший Шаг 6): Финальная очистка локального кэша (только после подтверждения удаления на бэкенде)
        # Это удаление всего хэша конфига шарда, включая список игроков, если он остался пустым.
        await self.guild_config_manager.delete_config(guild_id, shard_type)
        self.logger.success(f"Конфигурация (Hash) для гильдии {guild_id} (ключ '{RedisKeys.GUILD_CONFIG_HASH.format(shard_type=shard_type, guild_id=guild_id)}') удалена из локального кэша.")
        
        return {"status": "success", "message": "Лейаут Discord успешно удален и синхронизирован."}