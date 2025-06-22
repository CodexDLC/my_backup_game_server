# Discord_API/core/services/admin/game_server_layout_service.py

import logging
from typing import Dict, Any, List, Optional
import discord
from discord import Guild, CategoryChannel

# Импорт клиента для взаимодействия с нашим БЭКЕНДОМ (FastAPI)

# Импорт базовых операций Discord
from Discord_API.core.api_route_function.spec_route.discord_entity_api import DiscordBindingsAPI
from Discord_API.core.services.admin.base_discord_operations import BaseDiscordOperations
# Импорт конфигурации каналов
from Discord_API.core.assets.data.channels_config import CHANNELS_CONFIG

# Импортируем ваш централизованный логгер
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__)

class GameServerLayoutService:
    """
    Сервисный слой для управления лейаутом игрового сервера (шарда) Discord.
    Отвечает за:
    1. Чтение конфигурации game_server_layout из JSON.
    2. Создание категорий и каналов в Discord.
    3. Синхронизацию данных с FastAPI бэкендом.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.base_ops = BaseDiscordOperations(bot)
        self.backend_api = DiscordBindingsAPI()
        self.channels_config = CHANNELS_CONFIG

    async def setup_game_server_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Разворачивает минимальную структуру для игрового сервера (шарда) в Discord
        и синхронизирует с бэкендом.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден или недоступен.")

        game_layout = self.channels_config.get("game_server_layout")
        if not game_layout:
            raise ValueError("Конфигурация 'game_server_layout' не найдена в channels_config.json.")

        logger.info(f"Начало развертывания Game Server Layout для гильдии {guild_id} ('{guild.name}').")
        entities_to_sync_with_backend: List[Dict[str, Any]] = []
        
        created_categories = {} # {category_name: CategoryChannel_object}

        # Шаг 1: Создание всех категорий в Game Server Layout
        # Проходим по всем элементам верхнего уровня в game_layout (Категории Логи, Админ-зона, и списки категорий игроков)
        for key, value in game_layout.items():
            if key == "//":
                continue # Пропускаем комментарии

            if isinstance(value, dict) and value.get('type') == 'category':
                # Это новая вложенная категория (например, [ ЛОГИ СЕРВЕРА ], [ АДМИН-ЗОНА ])
                category_name = key
                category_data = value
                try:
                    category_channel = await self.base_ops.create_discord_category(
                        guild,
                        category_name,
                        permissions=category_data.get('permissions')
                    )
                    created_categories[category_name] = category_channel
                    entities_to_sync_with_backend.append({
                        "guild_id": guild_id,
                        "discord_id": category_channel.id,
                        "entity_type": category_data.get('type', 'category'),
                        "name": category_name,
                        "parent_id": None,
                        "permissions": category_data.get('permissions'),
                        "description": category_data.get('description')
                    })
                except Exception as e:
                    logger.error(f"Ошибка при создании/обновлении категории '{category_name}' в Game Server Layout: {e}", exc_info=True)
                    raise
            elif isinstance(value, list) and key == "player_channel_categories":
                # Это список категорий игрока
                for category_data_item in value:
                    if isinstance(category_data_item, dict) and category_data_item.get('type') == 'category':
                        category_name = category_data_item['name']
                        try:
                            category_channel = await self.base_ops.create_discord_category(
                                guild,
                                category_name,
                                permissions=category_data_item.get('permissions')
                            )
                            created_categories[category_name] = category_channel
                            entities_to_sync_with_backend.append({
                                "guild_id": guild_id,
                                "discord_id": category_channel.id,
                                "entity_type": category_data_item.get('type', 'category'),
                                "name": category_name,
                                "parent_id": None,
                                "permissions": category_data_item.get('permissions'),
                                "description": category_data_item.get('description')
                            })
                        except Exception as e:
                            logger.error(f"Ошибка при создании/обновлении категории игрока '{category_name}': {e}", exc_info=True)
                            raise

        # Шаг 2: Создание каналов внутри категорий в Game Server Layout
        # Проходим по тем же элементам верхнего уровня, но теперь ищем вложенные каналы
        for key, value in game_layout.items():
            if key == "//":
                continue

            if isinstance(value, dict) and value.get('type') == 'category' and "channels" in value:
                # Это категория с вложенными каналами (например, [ ЛОГИ СЕРВЕРА ], [ АДМИН-ЗОНА ])
                category_name = key
                category_data = value
                parent_category_channel = created_categories.get(category_name)
                
                if not parent_category_channel:
                    logger.warning(f"Родительская категория '{category_name}' не была создана, пропускаем каналы внутри Game Server Layout.")
                    continue

                for channel_name, channel_info in category_data["channels"].items():
                    try:
                        channel_obj = await self.base_ops.create_discord_channel(
                            guild,
                            channel_name,
                            channel_info.get('type', 'text'),
                            parent_category=parent_category_channel,
                            permissions=channel_info.get('permissions'),
                            description=channel_info.get('description')
                        )
                        if channel_obj:
                            entities_to_sync_with_backend.append({
                                "guild_id": guild_id,
                                "discord_id": channel_obj.id,
                                "entity_type": channel_info.get('type', 'text'),
                                "name": channel_name,
                                "parent_id": parent_category_channel.id,
                                "permissions": channel_info.get('permissions'),
                                "description": channel_info.get('description')
                            })
                    except Exception as e:
                        logger.error(f"Ошибка при создании/обновлении канала '{channel_name}' в категории '{category_name}' Game Server Layout: {e}", exc_info=True)
                        raise

        # Шаг 3: Отправка данных на бэкенд
        logger.info(f"Отправка {len(entities_to_sync_with_backend)} сущностей на бэкенд для синхронизации Game Server Layout...")
        try:
            sync_response = await self.backend_api.sync_discord_entities(entities_to_sync_with_backend)
            logger.info(f"Синхронизация Game Server Layout с бэкендом завершена: {sync_response.get('message')}")
            return {"status": "success", "message": sync_response.get('message'), "details": sync_response.get('data')}
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"Ошибка при синхронизации Game Server Layout с бэкендом: {e}")
            raise