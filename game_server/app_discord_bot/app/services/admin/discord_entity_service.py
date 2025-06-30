# game_server/app_discord_bot/app/services/admin/discord_entity_service.py
from typing import Dict, Any, List, Optional
import discord
import uuid

# Добавляем импорты для работы с кэшем
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.common_contracts.api_models.discord_api import GetDiscordEntitiesRequest, UnifiedEntityBatchDeleteRequest
from game_server.config.logging.logging_setup import app_logger as logger
# Добавляем импорт CacheSyncManager
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager

from .game_server_layout_service import GameServerLayoutService
from .hub_layout_service import HubLayoutService
from .role_management_service import RoleManagementService


class DiscordEntityService:
    """
    Высокоуровневый сервисный слой для управления сущностями Discord.
    Координирует операции развертывания и удаления лейаутов,
    используя кэш Redis с откатом до API бэкенда.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        if not hasattr(bot, 'request_helper'):
            logger.error("RequestHelper не инициализирован в объекте бота.")
            raise RuntimeError("RequestHelper не инициализирован.")
        self.request_helper: RequestHelper = bot.request_helper
        
        # Добавляем доступ к менеджеру кэша
        if not hasattr(bot, 'cache_manager') or not isinstance(bot.cache_manager, BotCache):
            logger.critical("BotCache не инициализирован в объекте бота.")
            raise RuntimeError("BotCache не инициализирован.")
        self.guild_config_manager = bot.cache_manager.guild_config

        # РЕФАКТОРИНГ: Получаем CacheSyncManager из объекта bot
        if not hasattr(bot, 'sync_manager'):
            logger.critical("CacheSyncManager (sync_manager) не инициализирован в объекте бота. Убедитесь, что он настроен через UtilsInitializer в main.py.")
            raise RuntimeError("CacheSyncManager не инициализирован.")
        self.cache_sync_manager: CacheSyncManager = bot.sync_manager

        # Сервисы теперь тоже должны получать доступ к боту с инициализированным кэшем
        self.game_server_layout_service = GameServerLayoutService(bot)
        self.hub_layout_service = HubLayoutService(bot)
        self.role_management_service = RoleManagementService(bot)
        self.logger = logger

    # Методы-прокси без изменений
    async def setup_game_server_layout(self, guild_id: int) -> Dict[str, Any]:
        return await self.game_server_layout_service.setup_game_server_layout(guild_id)

    async def setup_hub_layout(self, guild_id: int) -> Dict[str, Any]:
        return await self.hub_layout_service.setup_hub_layout(guild_id)

    async def sync_discord_roles(self, guild_id: int, message: Optional[discord.Message] = None) -> Dict[str, Any]:
        """
        РЕФАКТОРИНГ: Теперь принимает объект сообщения Discord для обновления прогресса.
        """
        return await self.role_management_service.sync_discord_roles(guild_id, message)

    async def teardown_discord_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Удаляет все сущности Discord для гильдии.
        Сначала пытается получить данные из кэша Redis. Если кэш пуст,
        обязательно обращается к бэкенду. После удаления очищает кэш.
        РЕФАКТОРИНГ: Теперь сначала удаляет конфигурацию на бэкенд-Redis, затем локально.
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            self.logger.warning(f"Гильдия с ID {guild_id} не найдена для удаления лейаута.")
            return {"status": "skipped", "message": f"Гильдия {guild_id} не найдена."}

        self.logger.info(f"Начало полного удаления лейаута Discord для гильдии {guild_id}.")
        
        entities_to_delete = []
        source = "Unknown"

        # Шаг 1: Пытаемся получить данные из кэша (ПРЕДПОЧТИТЕЛЬНЫЙ ИСТОЧНИК)
        cached_config = await self.guild_config_manager.get_all_fields(guild_id)

        if cached_config:
            self.logger.info(f"Данные для удаления получены из кэша Redis для гильдии {guild_id}.")
            source = "Redis Cache"
            
            if RedisKeys.FIELD_HUB_LAYOUT_CONFIG in cached_config:
                hub_layout_data = cached_config[RedisKeys.FIELD_HUB_LAYOUT_CONFIG]
                self.logger.debug(f"Парсинг Hub Layout из кэша.")
                for cat_name, cat_data in hub_layout_data.get('categories', {}).items():
                    entities_to_delete.append({'discord_id': cat_data['discord_id'], 'name': cat_name, 'entity_type': 'category'})
                    for chan_name, chan_data in cat_data.get('channels', {}).items():
                        entities_to_delete.append({'discord_id': chan_data['discord_id'], 'name': chan_name, 'entity_type': 'text_channel'})

            if RedisKeys.FIELD_LAYOUT_CONFIG in cached_config:
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

        # Шаг 2: Если кэш пуст ИЛИ не удалось получить из него данные, ОБРАЩАЕМСЯ К БЭКЕНДУ (Fallback/Гарантия)
        if not entities_to_delete: 
            self.logger.warning(f"Локальный кэш для гильдии {guild_id} пуст или не содержит сущностей для удаления. Запрашиваем данные у бэкенда.")
            source = "Backend DB (Fallback)"
            try:
                get_entities_payload = GetDiscordEntitiesRequest(guild_id=guild_id)
                response_data, _ = await self.request_helper.send_and_await_response(
                    api_method=self.request_helper.http_client_gateway.discord.get_entities,
                    request_payload=get_entities_payload,
                    correlation_id=get_entities_payload.correlation_id,
                    discord_context={"guild_id": guild_id, "command_source": "teardown_fallback"}
                )
                if not response_data or response_data.get("status") != "success":
                    raise RuntimeError(f"Бэкенд вернул ошибку при получении списка сущностей: {response_data.get('message', 'Неизвестная ошибка')}")
                
                retrieved_entities_from_backend = response_data.get("data", {}).get("entities", [])
                entities_to_delete.extend(retrieved_entities_from_backend)

            except Exception as e:
                self.logger.error(f"Критическая ошибка при получении данных от бэкенда для удаления: {e}", exc_info=True)
                return {"status": "failed", "message": f"Не удалось получить список сущностей для удаления: {e}"}

        # Если после всех попыток список сущностей все равно пуст
        if not entities_to_delete:
            self.logger.info(f"Не найдено сущностей для удаления для гильдии {guild_id} (проверены: {source}).")
            return {"status": "skipped", "message": "Нет сущностей для удаления."}

        self.logger.info(f"Найдено {len(entities_to_delete)} сущностей для удаления (источник: {source}).")

        # РЕФАКТОРИНГ: Шаг 3: Сначала удаляем конфигурацию гильдии из бэкенд-Redis
        self.logger.info(f"Инициируем удаление конфигурации гильдии {guild_id} из бэкенд-Redis через CacheSyncManager...")
        delete_success_on_backend_redis = await self.cache_sync_manager.delete_guild_config_from_backend(guild_id)
        
        if not delete_success_on_backend_redis:
            self.logger.error(f"Не удалось удалить конфигурацию гильдии {guild_id} из бэкенд-Redis. Отменяем дальнейшее удаление.")
            return {"status": "failed", "message": "Не удалось удалить конфигурацию из бэкенд-Redis."}
        
        self.logger.success(f"Конфигурация гильдии {guild_id} успешно удалена из бэкенд-Redis.")


        # Шаг 4: Удаляем сущности из Discord (логика почти без изменений)
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

        # Шаг 5: Отправляем запрос на массовое удаление сущностей Discord из БД
        if not discord_ids_to_delete:
            self.logger.info("Нет сущностей для удаления из БД (после попытки удаления из Discord).")
            return {"status": "success", "message": "Удаление не потребовалось."}
            
        delete_payload = UnifiedEntityBatchDeleteRequest(guild_id=guild_id, discord_ids=list(set(discord_ids_to_delete)))
        delete_response, _ = await self.request_helper.send_and_await_response(
            api_method=self.request_helper.http_client_gateway.discord.batch_delete_entities,
            request_payload=delete_payload,
            correlation_id=delete_payload.correlation_id,
            discord_context={"guild_id": guild_id, "command_source": "teardown_delete"}
        )

        if not delete_response or delete_response.get("status") != "success":
            raise RuntimeError("Бэкенд вернул ошибку при массовом удалении сущностей.")

        self.logger.success(f"Массовое удаление {len(discord_ids_to_delete)} сущностей из БД прошло успешно.")

        # РЕФАКТОРИНГ: Шаг 6: Финальная очистка локального кэша (только после подтверждения удаления на бэкенде)
        await self.guild_config_manager.delete_config(guild_id)
        self.logger.success(f"Конфигурация (Hash) для гильдии {guild_id} (ключ '{RedisKeys.GUILD_CONFIG_HASH.format(guild_id=guild_id)}') удалена из локального кэша.")
        
        return {"status": "success", "message": "Лейаут Discord успешно удален и синхронизирован."}
