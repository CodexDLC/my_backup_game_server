# app/services/admin/game_server_layout_service.py
from typing import Dict, Any, List, Optional
import discord
import uuid
import copy
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.common_contracts.api_models.discord_api import UnifiedEntitySyncRequest
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG

from .base_discord_operations import BaseDiscordOperations
from game_server.common_contracts.dtos.shard_dtos import SaveShardCommandDTO
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache
# УДАЛЕНО: Импорт CacheSyncManager, так как он теперь передается через объект bot
# from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
# НОВОЕ: Добавляем тайп-хинт для CacheSyncManager, чтобы не терять тип
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager


class GameServerLayoutService:
    """
    Сервисный слой для управления лейаутом игрового сервера (шарда) Discord.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.base_ops = BaseDiscordOperations(bot)
        self.channels_config = CHANNELS_CONFIG
        if not hasattr(bot, 'request_helper'):
            logger.error("RequestHelper не инициализирован в объекте бота. Убедитесь, что он настроен в main.py.")
            raise RuntimeError("RequestHelper не инициализирован.")
        self.request_helper: RequestHelper = bot.request_helper

        if not hasattr(bot, 'cache_manager') or not isinstance(bot.cache_manager, BotCache):
            logger.critical("BotCache не инициализирован в объекте бота. Необходим для сохранения конфигурации гильдии.")
            raise RuntimeError("BotCache не инициализирован. Убедитесь, что он настроен в main.py.")
        self.guild_config_manager = bot.cache_manager.guild_config

        # ИЗМЕНЕНО: Получаем CacheSyncManager из объекта bot
        if not hasattr(bot, 'sync_manager'):
            logger.critical("CacheSyncManager (sync_manager) не инициализирован в объекте бота. Убедитесь, что он настроен через UtilsInitializer в main.py.")
            raise RuntimeError("CacheSyncManager не инициализирован.")
        self.cache_sync_manager: CacheSyncManager = bot.sync_manager

        self.permissions_sets = self.channels_config.get("permissions_sets", {})


    async def setup_game_server_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Разворачивает структуру игрового шарда в Discord, синхронизирует с бэкендом,
        регистрирует шард и кэширует его конфигурацию в Redis.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord server with ID {guild_id} not found.")

        game_layout_config_original = self.channels_config.get("game_server_layout")
        if not game_layout_config_original:
            raise ValueError("Конфигурация 'game_server_layout' не найдена.")

        logger.info(f"Начало развертывания Game Server Layout для гильдии {guild_id}.")
        entities_to_sync: List[Dict[str, Any]] = []
        created_categories: Dict[str, discord.CategoryChannel] = {}

        welcome_channel_id: Optional[int] = None
        player_channel_category_ids_map: Dict[str, int] = {} 
        
        # ОБНОВЛЕНИЕ: Инициализируем структуру для кэширования в Redis как словари по именам
        cached_layout_for_redis: Dict[str, Any] = {
            "categories": {}, # Теперь это словарь, где ключ - имя категории
            "player_channel_categories": {} # Теперь это словарь, где ключ - имя категории
        }

        # Шаг 1: Создание категорий верхнего уровня (ЛОГИ СЕРВЕРА, АДМИН-ЗОНА, ОБЩИЕ КАНАЛЫ)
        for key, value in game_layout_config_original.items():
            if isinstance(value, dict) and value.get('type') == 'category':
                try:
                    permissions_key = value.get('permissions')
                    permissions_data = self.permissions_sets.get(permissions_key, {})
                    if not permissions_data and permissions_key:
                        logger.warning(f"Набор разрешений '{permissions_key}' не найден в permissions_sets.")

                    category = await self.base_ops.create_discord_category(guild, key, permissions_data)
                    created_categories[key] = category
                    
                    # ОБНОВЛЕНИЕ: Добавляем категорию в структуру для Redis (только имя и ID)
                    cached_layout_for_redis["categories"][key] = { # Добавляем по ключу
                        "discord_id": category.id,
                        "name": category.name,
                        "channels": {} # Подготовка для каналов внутри
                    }

                    entities_to_sync.append({
                        "discord_id": category.id,
                        "entity_type": "category",
                        "name": category.name,
                        "permissions": permissions_key,
                        "description": value.get('description'),
                        "parent_id": None,
                        "access_code": None,
                        "guild_id": guild_id
                    })
                except Exception as e:
                    logger.error(f"Ошибка при создании категории '{key}': {e}", exc_info=True)
                    raise

        # Создание категорий игроков из списка 'player_channel_categories'
        player_categories_config = game_layout_config_original.get("player_channel_categories", [])
        for category_info in player_categories_config:
            if isinstance(category_info, dict) and category_info.get('type') == 'category':
                try:
                    category_name = category_info.get('name')
                    permissions_key = category_info.get('permissions')
                    description = category_info.get('description')

                    permissions_data = self.permissions_sets.get(permissions_key, {})
                    if not permissions_data and permissions_key:
                        logger.warning(f"Набор разрешений '{permissions_key}' не найден в permissions_sets для категории игрока.")

                    player_category = await self.base_ops.create_discord_category(guild, category_name, permissions_data)
                    created_categories[category_name] = player_category
                    player_channel_category_ids_map[category_name] = player_category.id
                    
                    # ОБНОВЛЕНИЕ: Добавляем категорию игрока в структуру для Redis (только имя и ID)
                    cached_layout_for_redis["player_channel_categories"][category_name] = { # Добавляем по ключу
                        "discord_id": player_category.id,
                        "name": player_category.name,
                        "channels": {}
                    }

                    entities_to_sync.append({
                        "discord_id": player_category.id,
                        "entity_type": "category",
                        "name": player_category.name,
                        "permissions": permissions_key,
                        "description": description,
                        "parent_id": None,
                        "access_code": None,
                        "guild_id": guild_id
                    })
                except Exception as e:
                    logger.error(f"Ошибка при создании категории игрока '{category_name}': {e}", exc_info=True)
                    raise

        # Шаг 2: Создание каналов внутри категорий
        for cat_name, parent_cat_obj in created_categories.items():
            cat_data_original_for_channels = None
            if cat_name in game_layout_config_original and isinstance(game_layout_config_original[cat_name], dict):
                cat_data_original_for_channels = game_layout_config_original[cat_name]
            else:
                # Если категория не верхнего уровня, ищем ее в player_channel_categories
                for pc_cat_item in game_layout_config_original.get("player_channel_categories", []):
                    if isinstance(pc_cat_item, dict) and pc_cat_item.get('name') == cat_name:
                        cat_data_original_for_channels = pc_cat_item
                        break
            
            if not cat_data_original_for_channels or "channels" not in cat_data_original_for_channels:
                continue 

            channels_info = cat_data_original_for_channels.get("channels", {})
            
            for chan_name, chan_info in channels_info.items():
                try:
                    raw_channel_type_from_config = chan_info.get('type', 'text')
                    
                    entity_type_for_dto = raw_channel_type_from_config
                    if raw_channel_type_from_config == 'text':
                        entity_type_for_dto = 'text_channel'
                    elif raw_channel_type_from_config == 'voice':
                        entity_type_for_dto = 'voice_channel'
                    
                    if entity_type_for_dto not in ['category', 'text_channel', 'voice_channel', 'role', 'user', 'guild', 'news', 'forum']:
                        logger.warning(f"Неизвестный тип канала '{raw_channel_type_from_config}' в конфиге для канала '{chan_name}'. Пропуск синхронизации для этого канала.")
                        continue
                    
                    permissions_key = chan_info.get('permissions')
                    permissions_data = self.permissions_sets.get(permissions_key, {})
                    if not permissions_data and permissions_key:
                        logger.warning(f"Набор разрешений '{permissions_key}' не найден в permissions_sets для канала.")

                    channel = await self.base_ops.create_discord_channel(
                        guild,
                        chan_name,
                        raw_channel_type_from_config,
                        parent_cat_obj,
                        permissions_data,
                        chan_info.get('description')
                    )
                    if channel:
                        # ОБНОВЛЕНИЕ: Добавляем канал в структуру для Redis (только имя, ID, parent_id)
                        target_category_channels_dict = None
                        if cat_name in cached_layout_for_redis["categories"]:
                            target_category_channels_dict = cached_layout_for_redis["categories"][cat_name]["channels"]
                        elif cat_name in cached_layout_for_redis["player_channel_categories"]: # Ищем в player_channel_categories
                             target_category_channels_dict = cached_layout_for_redis["player_channel_categories"][cat_name]["channels"]
                        
                        if target_category_channels_dict is not None:
                            target_category_channels_dict[chan_name] = {
                                "discord_id": channel.id,
                                "name": channel.name,
                                "parent_id": parent_cat_obj.id
                            }


                        entities_to_sync.append({
                            "discord_id": channel.id,
                            "entity_type": entity_type_for_dto,
                            "name": channel.name,
                            "parent_id": parent_cat_obj.id,
                            "permissions": permissions_key,
                            "description": chan_info.get('description'),
                            "access_code": None,
                            "guild_id": guild_id
                        })
                        if chan_name == "приёмная":
                            welcome_channel_id = channel.id

                except Exception as e:
                    logger.error(f"Ошибка при создании канала '{chan_name}': {e}", exc_info=True)
                    raise
        
        # Шаг 3: Синхронизация сущностей Discord с бэкендом
        if not entities_to_sync:
            logger.warning("Не было создано ни одной сущности Discord для синхронизации.")
            return {"status": "success", "message": "Нет сущностей Discord для синхронизации, регистрация шарда отменена."}

        logger.info(f"Отправка {len(entities_to_sync)} сущностей Discord на бэкенд для синхронизации...")

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
            response_sync_discord, retrieved_context_sync_discord = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_entities,
                request_payload=discord_sync_request_payload,
                correlation_id=discord_sync_request_payload.correlation_id,
                discord_context=discord_sync_context
            )

            if response_sync_discord and response_sync_discord.get("status") == "success":
                logger.success("Синхронизация Discord сущностей успешно завершена.")
            else:
                error_msg = response_sync_discord.get('message') if response_sync_discord else "Нет ответа от сервера"
                logger.error(f"Получен ответ с ошибкой при синхронизации Discord сущностей, контекст: {retrieved_context_sync_discord}. Ошибка: {error_msg}")
                raise RuntimeError(f"Бэкенд вернул ошибку при синхронизации Discord сущностей: {error_msg}")
        except Exception as e:
            logger.error(f"Критическая ошибка при вызове API синхронизации Discord сущностей: {e}", exc_info=True)
            raise RuntimeError(f"Критическая ошибка при синхронизации Discord сущностей: {e}")


        # Шаг 4: Регистрация (сохранение) шарда на бэкенде
        logger.info(f"Регистрация игрового шарда {guild.name} (ID: {guild_id}) на бэкенде...")

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

        try:
            response_register_shard, retrieved_context_register_shard = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.shard.register,
                request_payload=shard_register_payload,
                correlation_id=shard_register_payload.correlation_id,
                discord_context=shard_register_context
            )

            if response_register_shard and response_register_shard.get("status") == "success":
                logger.success(f"Игровой шард {guild.name} (ID: {guild_id}) успешно зарегистрирован на бэкенде.")
                
                # ШАГ 5: КЭШИРОВАНИЕ КОНФИГУРАЦИИ ЛЕЙАУТА В REDIS (ИЗМЕНЕННАЯ ЛОГИКА)
                try:
                    # Проверяем, есть ли что кэшировать
                    if cached_layout_for_redis["categories"] or cached_layout_for_redis["player_channel_categories"]:
                        
                        # Готовим объект данных именно для этого поля
                        layout_data_to_cache = {
                            "welcome_channel_id": welcome_channel_id,
                            "player_channel_category_map": player_channel_category_ids_map,
                            "layout_structure": cached_layout_for_redis
                        }

                        # Используем новый универсальный метод менеджера
                        await self.guild_config_manager.set_field(
                            guild_id=guild_id,
                            field_name=RedisKeys.FIELD_LAYOUT_CONFIG, # Используем константу для имени поля
                            data=layout_data_to_cache # Сохраняем только данные лейаута
                        )
                        logger.success(f"Поле '{RedisKeys.FIELD_LAYOUT_CONFIG}' для гильдии {guild_id} сохранено в кэше.")

                        # НОВОЕ: Шаг 6: Отправка полной конфигурации гильдии из локального кэша на бэкенд
                        logger.info(f"Запускаем синхронизацию полной конфигурации гильдии {guild_id} с бэкендом через CacheSyncManager...")
                        sync_success = await self.cache_sync_manager.sync_guild_config_to_backend(guild_id)
                        if sync_success:
                            logger.success(f"Полная конфигурация гильдии {guild_id} успешно синхронизирована с бэкендом.")
                        else:
                            logger.error(f"Ошибка при синхронизации полной конфигурации гильдии {guild_id} с бэкендом.")

                    else:
                        logger.warning(f"Нет данных о лейауте для кэширования для гильдии {guild_id}.")

                except Exception as e:
                    # Логируем ошибку кэширования, но не прерываем основной процесс,
                    # так как регистрация на бэкенде уже прошла успешно.
                    logger.error(f"Не удалось закэшировать конфигурацию лейаута для гильдии {guild_id}: {e}", exc_info=True)

                return {"status": "success", "message": "Развертывание и регистрация шарда завершены.", "details": response_register_shard.get('data')}
            else:
                error_msg = response_register_shard.get('message') if response_register_shard else "Нет ответа от сервера"
                logger.error(f"Получен ответ с ошибкой при регистрации шарда, контекст: {retrieved_context_register_shard}. Ошибка: {error_msg}")
                raise RuntimeError(f"Бэкенд вернул ошибку при регистрации шарда: {error_msg}")
        except Exception as e:
            logger.error(f"Критическая ошибка при вызове API регистрации шарда: {e}", exc_info=True)
            raise RuntimeError(f"Критическая ошибка при регистрации шарда: {e}")
