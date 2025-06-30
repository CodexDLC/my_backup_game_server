# app/services/admin/hub_layout_service.py

from typing import Dict, Any, List
import discord
import uuid
from pydantic import ValidationError

from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.common_contracts.api_models.discord_api import UnifiedEntitySyncRequest
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG
from .base_discord_operations import BaseDiscordOperations
# Добавляем импорты CacheSyncManager
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
# Добавляем импорт RedisKeys
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache


class HubLayoutService:
    """
    Сервисный слой для управления лейаутом Хаб-сервера.
    Отвечает за создание структуры в Discord и отправку всех сущностей
    на бэкенд единым пакетом для синхронизации.
    """
    def __init__(self, bot):
        self.bot = bot
        self.base_ops = BaseDiscordOperations(bot)
        self.channels_config = CHANNELS_CONFIG
        if not hasattr(bot, 'request_helper'):
            logger.error("RequestHelper не инициализирован в объекте бота. Убедитесь, что он настроен в main.py.")
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


    async def setup_hub_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Разворачивает полную структуру хаб-сервера в Discord и синхронизирует
        ее с бэкендом одним запросом.
        РЕФАКТОРИНГ: После синхронизации с БД, кэширует в локальный Redis и затем полностью
        синхронизирует локальный кэш гильдии с бэкенд-Redis.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден.")

        hub_layout = self.channels_config.get("hub_layout")
        if not hub_layout:
            raise ValueError("Конфигурация 'hub_layout' не найдена. Проверьте channels_config.py")

        logger.info(f"Начало развертывания Hub Layout для гильдии {guild_id}.")

        entities_to_sync: List[Dict[str, Any]] = []
        created_categories: Dict[str, discord.CategoryChannel] = {}

        # РЕФАКТОРИНГ: Инициализируем структуру для кэширования в Redis
        cached_hub_layout_for_redis: Dict[str, Any] = {
            "categories": {}
        }


        # --- Шаг 1: Создаем категории в Discord и готовим их для синхронизации ---
        for category_name, category_data in hub_layout.items():
            if not isinstance(category_data, dict) or category_data.get('type') != 'category':
                continue
            
            try:
                permissions_key = category_data.get('permissions')
                permissions_data = {}
                if isinstance(permissions_key, str):
                    permissions_data = self.channels_config.get('permissions_sets', {}).get(permissions_key, {})
                elif isinstance(permissions_key, dict):
                    permissions_data = permissions_key

                category_channel = await self.base_ops.create_discord_category(
                    guild, category_name, permissions=permissions_data
                )
                created_categories[category_name] = category_channel
                
                entities_to_sync.append({
                    "discord_id": category_channel.id,
                    "entity_type": "category",
                    "name": category_channel.name,
                    "description": category_data.get('description'),
                    "parent_id": None,
                    "permissions": permissions_key,
                    "access_code": None,
                    "guild_id": guild_id
                })
                # РЕФАКТОРИНГ: Добавляем категорию в структуру для Redis
                cached_hub_layout_for_redis["categories"][category_name] = {
                    "discord_id": category_channel.id,
                    "name": category_channel.name,
                    "channels": {} # Подготовка для каналов внутри
                }

            except Exception as e:
                logger.error(f"Ошибка при создании категории '{category_name}': {e}", exc_info=True)
                raise

        # --- Шаг 2: Создаем каналы внутри категорий и готовим их для синхронизации ---
        for category_name, category_data in hub_layout.items():
            if "channels" not in category_data:
                continue

            parent_category = created_categories.get(category_name)
            if not parent_category:
                logger.warning(f"Категория-родитель '{category_name}' не найдена, пропускаем дочерние каналы.")
                continue

            for channel_name, channel_info in category_data["channels"].items():
                try:
                    entity_type_for_channel = channel_info.get('type', 'text')
                    if entity_type_for_channel == 'text':
                        entity_type_for_channel = 'text_channel'

                    channel_permissions_key = channel_info.get('permissions')
                    channel_permissions_data = {}
                    if isinstance(channel_permissions_key, str):
                        channel_permissions_data = self.channels_config.get('permissions_sets', {}).get(channel_permissions_key, {})
                    elif isinstance(channel_permissions_key, dict):
                        channel_permissions_data = channel_permissions_key


                    channel_obj = await self.base_ops.create_discord_channel(
                        guild, channel_name, entity_type_for_channel,
                        parent_category=parent_category, permissions=channel_permissions_data,
                        description=channel_info.get('description')
                    )
                    if channel_obj:
                        entities_to_sync.append({
                            "discord_id": channel_obj.id,
                            "entity_type": entity_type_for_channel,
                            "name": channel_obj.name,
                            "description": channel_info.get('description'),
                            "parent_id": parent_category.id,
                            "permissions": channel_permissions_key,
                            "access_code": None,
                            "guild_id": guild_id
                        })
                        # РЕФАКТОРИНГ: Добавляем канал в структуру для Redis
                        if category_name in cached_hub_layout_for_redis["categories"]:
                            cached_hub_layout_for_redis["categories"][category_name]["channels"][channel_name] = {
                                "discord_id": channel_obj.id,
                                "name": channel_obj.name,
                                "parent_id": parent_category.id
                            }


                except Exception as e:
                    logger.error(f"Ошибка при создании канала '{channel_name}': {e}", exc_info=True)
                    raise
                
        # --- Шаг 3: Отправка ВСЕХ собранных сущностей на бэкенд одним запросом ---
        if not entities_to_sync:
            logger.warning("Не было создано ни одной сущности для синхронизации.")
            return {"status": "success", "message": "Нет сущностей для синхронизации."}

        logger.info(f"Отправка {len(entities_to_sync)} сущностей на бэкенд для синхронизации...")
        
        discord_context = {
            "user_id": self.bot.user.id,
            "guild_id": guild_id,
            "command_source": "setup_hub_layout"
        }

        try:
            # Pydantic DTO уже должен иметь поле client_id, если бэкенд его ожидает.
            # Мы не добавляем его здесь, чтобы не менять сигнатуру, если она не требует client_id.
            request_payload = UnifiedEntitySyncRequest(guild_id=guild_id, entities_data=entities_to_sync)

            logger.info("HubLayoutService: Pydantic-модель UnifiedEntitySyncRequest успешно создана.")

            response, retrieved_context = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_entities,
                request_payload=request_payload,
                correlation_id=request_payload.correlation_id,
                discord_context=discord_context
            )

            # Проверяем response.get('status') == 'success'
            if response and response.get("status") == "success":
                logger.info("Синхронизация Hub Layout с бэкендом успешно завершена.")
                
                # РЕФАКТОРИНГ: Шаг 4: Кэширование конфигурации Hub Layout в Redis (локально)
                try:
                    if cached_hub_layout_for_redis["categories"]: # Проверяем, есть ли категории для кэширования
                        await self.guild_config_manager.set_field(
                            guild_id=guild_id,
                            field_name=RedisKeys.FIELD_HUB_LAYOUT_CONFIG, # Используем новую константу
                            data=cached_hub_layout_for_redis # Сохраняем собранные данные
                        )
                        logger.success(f"Поле '{RedisKeys.FIELD_HUB_LAYOUT_CONFIG}' для гильдии {guild_id} сохранено в кэше.")

                        # РЕФАКТОРИНГ: Шаг 5: Запускаем синхронизацию полной конфигурации гильдии с бэкендом
                        logger.info(f"Запускаем синхронизацию полной конфигурации гильдии {guild_id} с бэкендом через CacheSyncManager после развертывания Hub Layout...")
                        sync_success_to_backend = await self.cache_sync_manager.sync_guild_config_to_backend(guild_id)
                        if sync_success_to_backend:
                            logger.success(f"Полная конфигурация гильдии {guild_id} успешно синхронизирована с бэкендом после развертывания Hub Layout.")
                        else:
                            logger.error(f"Ошибка при синхронизации полной конфигурации гильдии {guild_id} с бэкендом после развертывания Hub Layout.")

                    else:
                        logger.warning(f"Нет данных о Hub Layout для кэширования для гильдии {guild_id}.")

                except Exception as e:
                    logger.error(f"Не удалось закэшировать Hub Layout для гильдии {guild_id} или синхронизировать с бэкендом: {e}", exc_info=True)


                return {"status": "success", "message": response.get('message'), "details": response.get('data')}
            else:
                error_msg = response.get('message') if response else "Нет ответа от сервера"
                logger.error(f"Получен ответ с ошибкой, контекст: {retrieved_context}. Ошибка: {error_msg}")
                raise RuntimeError(f"Бэкенд вернул ошибку при синхронизации: {error_msg}")
        except ValidationError as e:
            logger.error(f"HubLayoutService: Ошибка валидации Pydantic для UnifiedEntitySyncRequest: {e.errors()}", exc_info=True)
            raise RuntimeError(f"Ошибка валидации данных для синхронизации: {e.errors()}")
        except Exception as e:
            logger.error(f"Критическая ошибка при вызове API синхронизации: {e}", exc_info=True)
            raise
