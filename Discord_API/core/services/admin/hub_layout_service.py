# Discord_API/core/services/admin/hub_layout_service.py

import logging
from typing import Dict, Any, List, Optional
import discord
from discord import Guild

# Импорт клиента для взаимодействия с нашим БЭКЕНДОМ (FastAPI)

# Импорт базовых операций Discord
from Discord_API.core.api_route_function.spec_route.discord_entity_api import DiscordBindingsAPI
from Discord_API.core.services.admin.base_discord_operations import BaseDiscordOperations
# Импорт конфигурации каналов
from Discord_API.core.assets.data.channels_config import CHANNELS_CONFIG

# Импортируем ваш централизованный логгер
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__)

class HubLayoutService:
    """
    Сервисный слой для управления лейаутом публичного Хаб-сервера Discord.
    Отвечает за:
    1. Чтение конфигурации hub_layout из JSON.
    2. Создание категорий и каналов в Discord.
    3. Синхронизацию данных с FastAPI бэкендом.
    4. Удаление всего лейаута Хаба.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.base_ops = BaseDiscordOperations(bot)
        self.backend_api = DiscordBindingsAPI()
        self.channels_config = CHANNELS_CONFIG

    async def setup_hub_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Разворачивает полную структуру хаб-сервера в Discord и синхронизирует с бэкендом.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден или недоступен.")

        hub_layout = self.channels_config.get("hub_layout")
        if not hub_layout:
            raise ValueError("Конфигурация 'hub_layout' не найдена в channels_config.json.")

        logger.info(f"Начало развертывания Hub Layout для гильдии {guild_id} ('{guild.name}').")

        entities_to_sync_with_backend: List[Dict[str, Any]] = []
        created_categories = {} # {original_name: discord.CategoryChannel}

        # Шаг 1: Создание категорий в Discord
        # Сначала создаем все категории, чтобы у нас были их Discord ID
        for category_name, category_data in hub_layout.items():
            if not isinstance(category_data, dict) or category_data.get('type') != 'category':
                continue # Пропускаем комментарии "//" и не-категории
            
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
                logger.error(f"Ошибка при создании/обновлении категории '{category_name}': {e}", exc_info=True)
                raise # Пробрасываем ошибку выше

        # Шаг 2: Создание каналов внутри категорий в Discord
        for category_name, category_data in hub_layout.items():
            if not isinstance(category_data, dict) or category_data.get('type') != 'category' or "channels" not in category_data:
                continue

            parent_category_channel = created_categories.get(category_name)
            if not parent_category_channel:
                logger.warning(f"Родительская категория '{category_name}' не была создана, пропускаем каналы внутри.")
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
                    logger.error(f"Ошибка при создании/обновлении канала '{channel_name}' в категории '{category_name}': {e}", exc_info=True)
                    raise

        # Шаг 3: Отправка данных на бэкенд для синхронизации
        logger.info(f"Отправка {len(entities_to_sync_with_backend)} сущностей на бэкенд для синхронизации Hub Layout...")
        try:
            sync_response = await self.backend_api.sync_discord_entities(entities_to_sync_with_backend)
            logger.info(f"Синхронизация Hub Layout с бэкендом завершена: {sync_response.get('message')}")
            return {"status": "success", "message": sync_response.get('message'), "details": sync_response.get('data')}
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"Ошибка при синхронизации Hub Layout с бэкендом: {e}")
            raise


    async def teardown_discord_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Полностью удаляет все Discord сущности (категории, каналы),
        связанные с данной гильдией, как из Discord, так и из бэкенда.
        Этот метод будет общим для Hub и Game Server лейаутов.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден или недоступен.")

        logger.info(f"Начало удаления всех Discord сущностей для гильдии {guild_id} ('{guild.name}').")

        # 1. Получаем список сущностей из бэкенда (из нашей БД)
        try:
            get_response = await self.backend_api.get_discord_entities_by_guild(guild_id)
            if not get_response.get('success'):
                error_message = get_response.get('error', {}).get('message', 'Неизвестная ошибка.')
                raise RuntimeError(f"Ошибка при получении сущностей из бэкенда: {error_message}")
            
            entities_data_from_backend = get_response.get('data', {}).get('entities', [])
            
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"Ошибка при получении сущностей из бэкенда для удаления: {e}")
            raise ValueError(f"Не удалось получить список сущностей из БД для удаления: {e}")

        if not entities_data_from_backend:
            logger.info(f"Для гильдии {guild_id} не найдено сущностей в БД для удаления.")
            return {"status": "success", "message": "Не найдено сущностей для удаления."}

        # Отсортировать сущности так, чтобы каналы удалялись перед категориями
        # (Категории должны быть удалены после каналов)
        # 0 - каналы (text, voice, forum, news), 1 - категории
        sorted_entities = sorted(entities_data_from_backend, key=lambda x: 0 if x.get('entity_type') not in ['category'] else 1) 

        discord_ids_successfully_deleted_from_discord: List[int] = []

        # 2. Удаление сущностей из Discord
        for entity_data in sorted_entities:
            discord_id = entity_data.get('discord_id')
            entity_name = entity_data.get('name')
            entity_type = entity_data.get('entity_type')

            if not discord_id:
                logger.warning(f"Сущность '{entity_name}' ({entity_type}) не имеет Discord ID, пропускаем удаление из Discord.")
                continue
            
            try:
                discord_obj = await self.base_ops.get_discord_object_by_id(guild, discord_id)

                if discord_obj:
                    await self.base_ops.delete_discord_entity(discord_obj)
                    discord_ids_successfully_deleted_from_discord.append(discord_id)
                else:
                    logger.warning(f"Discord сущность '{entity_name}' (ID: {discord_id}) не найдена в Discord, возможно уже удалена.")
                    discord_ids_successfully_deleted_from_discord.append(discord_id) # Все равно добавим для удаления из БД, если ее нет в Discord
            except Exception as e:
                logger.error(f"Ошибка при удалении сущности '{entity_name}' (ID: {discord_id}) из Discord: {e}", exc_info=True)
                raise # Если возникла ошибка при удалении из Discord, пробрасываем её

        # 3. Отправка запроса на бэкенд для удаления из нашей БД
        if discord_ids_successfully_deleted_from_discord:
            logger.info(f"Отправка {len(discord_ids_successfully_deleted_from_discord)} сущностей на бэкенд для удаления из БД...")
            try:
                delete_response = await self.backend_api.delete_discord_entities_batch(guild_id, discord_ids_successfully_deleted_from_discord)
                logger.info(f"Удаление из бэкенда завершено: {delete_response.get('message')}. Удалено: {delete_response.get('data', {}).get('deleted_count')}")
                return {"status": "success", "message": delete_response.get('message'), "details": delete_response.get('data')}
            except (ConnectionError, ValueError, RuntimeError) as e:
                logger.error(f"Ошибка при удалении из бэкенда: {e}")
                raise
        else:
            return {"status": "success", "message": "Нечего удалять из БД."}