# Discord_API/core/services/admin/article_management_service.py

from typing import Dict, Any, Optional
import discord
from discord import Guild, TextChannel, CategoryChannel, utils

# Импорт клиента для взаимодействия с нашим БЭКЕНДОМ (FastAPI)
from Discord_API.core.api_route_function.spec_route.discord_entity_api import DiscordBindingsAPI
# Импорт базовых операций Discord
from Discord_API.core.services.admin.base_discord_operations import BaseDiscordOperations
# Импорт конфигурации каналов


# Импортируем ваш централизованный логгер
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
from Discord_API.core.assets.data.channels_config import CHANNELS_CONFIG
logger = bot_logger.getChild(__name__) # Создаем дочерний логгер для этого модуля

class ArticleManagementService:
    """
    Сервисный слой для управления каналами-статьями (например, в "Библиотеке Знаний").
    Отвечает за:
    1. Поиск родительской категории в Discord.
    2. Создание нового канала-статьи в Discord.
    3. Отправку данных о созданном канале на FastAPI бэкенд.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.base_ops = BaseDiscordOperations(bot)
        self.backend_api = DiscordBindingsAPI()
        self.channels_config = CHANNELS_CONFIG

    async def add_article_channel(self, guild_id: int, channel_name: str) -> Dict[str, Any]:
        """
        Добавляет новый текстовый канал-статью в категорию "Библиотека Знаний" в Discord
        и синхронизирует его с бэкендом.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден или недоступен.")

        # Получаем имя категории "Библиотека Знаний" из конфигурации, если оно там есть
        knowledge_category_name = None
        for cat_name, cat_data in self.channels_config.get("hub_layout", {}).items():
            if "БИБЛИОТЕКА ЗНАНИЙ" in cat_name: # Более гибкий поиск по подстроке
                knowledge_category_name = cat_name
                break
        
        if not knowledge_category_name:
            # Если не найдено в конфиге, используем хардкод (или выдаем ошибку)
            knowledge_category_name = "Категория: [ БИБЛИОТЕКА ЗНАНИЙ ] 📚"
            logger.warning(f"Имя категории 'Библиотека Знаний' не найдено в channels_config.json. Используем хардкод: '{knowledge_category_name}'.")

        logger.info(f"Попытка добавить канал '{channel_name}' в категорию '{knowledge_category_name}' для гильдии {guild_id}.")

        # 1. Находим родительскую категорию в Discord
        parent_category = utils.get(guild.categories, name=knowledge_category_name)
        if not parent_category:
            raise ValueError(f"Категория '{knowledge_category_name}' не найдена на сервере Discord. Невозможно создать канал.")

        # 2. Создаем канал в Discord с помощью base_ops
        new_channel_discord_obj: Optional[TextChannel] = None
        try:
            new_channel_discord_obj = await self.base_ops.create_discord_channel(
                guild,
                channel_name,
                "text", # Тип канала - текстовый
                parent_category=parent_category,
                permissions="read_only",
                description="Статья из Библиотеки Знаний."
            )
            logger.info(f"Канал '{channel_name}' успешно создан в Discord (ID: {new_channel_discord_obj.id}).")
        except Exception as e: # base_ops уже логирует и пробрасывает специфические ошибки
            raise ValueError(f"Не удалось создать канал в Discord: {e}")

        if not new_channel_discord_obj:
            raise RuntimeError("Не удалось создать канал в Discord, объект не был возвращен.")

        # 3. Отправляем данные о созданном канале на бэкенд для сохранения в БД
        entity_data_for_backend = {
            "guild_id": guild_id,
            "discord_id": new_channel_discord_obj.id,
            "entity_type": "text_channel",
            "name": channel_name,
            "parent_id": parent_category.id,
            "permissions": "read_only",
            "description": "Статья из Библиотеки Знаний."
        }
        try:
            create_response = await self.backend_api.create_single_discord_entity(entity_data_for_backend)
            if not create_response.get('success'):
                error_msg = create_response.get('error', {}).get('message', 'Неизвестная ошибка.')
                raise RuntimeError(f"Бэкенд вернул ошибку при сохранении канала: {error_msg}")

            logger.info(f"Данные о канале '{channel_name}' успешно отправлены на бэкенд для сохранения.")
            return {"status": "success", "message": create_response.get('message'), "details": create_response.get('data')}
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"Ошибка при синхронизации созданного канала с бэкендом: {e}", exc_info=True)
            await self.base_ops.delete_discord_entity(new_channel_discord_obj)
            logger.warning(f"Откат: канал '{channel_name}' (ID: {new_channel_discord_obj.id}) удален из Discord из-за ошибки синхронизации с бэкендом.")
            raise ValueError(f"Не удалось сохранить канал в базе данных: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при синхронизации созданного канала с бэкендом: {e}", exc_info=True)
            await self.base_ops.delete_discord_entity(new_channel_discord_obj)
            logger.warning(f"Откат: канал '{channel_name}' (ID: {new_channel_discord_obj.id}) удален из Discord из-за непредвиденной ошибки синхронизации с бэкендом.")
            raise