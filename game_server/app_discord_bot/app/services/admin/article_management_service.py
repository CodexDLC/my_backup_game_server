# app/services/admin/article_management_service.py
from typing import Dict, Any, Optional, List
import discord
from discord import TextChannel, utils
import uuid # НОВЫЙ ИМПОРТ: uuid, если не используется в request_helper

from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.common_contracts.api_models.discord_api import UnifiedEntitySyncRequest
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG

from .base_discord_operations import BaseDiscordOperations


class ArticleManagementService:
    """
    Сервисный слой для управления каналами-статьями.
    Создает канал в Discord и отправляет его на бэкенд для синхронизации.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.base_ops = BaseDiscordOperations(bot)
        self.channels_config = CHANNELS_CONFIG
        # НОВОЕ: Инициализация RequestHelper
        if not hasattr(bot, 'request_helper'):
            logger.error("RequestHelper не инициализирован в объекте бота. Убедитесь, что он настроен в main.py.")
            raise RuntimeError("RequestHelper не инициализирован.")
        self.request_helper: RequestHelper = bot.request_helper


    async def add_article_channel(self, guild_id: int, channel_name: str) -> Dict[str, Any]:
        """
        Добавляет новый текстовый канал-статью и синхронизирует его с бэкендом.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден.")
        
        # Поиск категории "Библиотека Знаний"
        knowledge_category_name = next(
            (cat_name for cat_name in self.channels_config.get("hub_layout", {})
             # 🔥 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ ЗДЕСЬ
             if "БИБЛИОТЕКА ЗНАНИЙ" in cat_name), # Удален невалидный текст "ИЗМЕНЕНО: на 'БИБЛИОТЕКА ЗНАНИЙ' - 'knowledge_category_name'"
            "Категория: [ БИБЛИОТЕКА ЗНАНИЙ ] 📚" # Имя по умолчанию
        )

        logger.info(f"Попытка добавить канал '{channel_name}' в категорию '{knowledge_category_name}'.")
        parent_category = utils.get(guild.categories, name=knowledge_category_name)
        if not parent_category:
            raise ValueError(f"Категория '{knowledge_category_name}' не найдена на сервере.")

        # 2. Создаем канал в Discord (без изменений)
        new_channel_obj: Optional[TextChannel] = None
        try:
            new_channel_obj = await self.base_ops.create_discord_channel(
                guild, channel_name, "text", parent_category=parent_category,
                permissions="read_only", description="Статья из Библиотеки Знаний."
            )
            if not new_channel_obj:
                raise RuntimeError("Не удалось создать канал в Discord, объект не был возвращен.")
            logger.success(f"Канал '{channel_name}' успешно создан в Discord (ID: {new_channel_obj.id}).")
        except Exception as e:
            logger.error(f"Ошибка при создании канала '{channel_name}' в Discord: {e}", exc_info=True)
            raise ValueError(f"Не удалось создать канал в Discord: {e}")

        # 3. Отправляем данные на бэкенд через единый API синхронизации
        entity_data = {
            "discord_id": new_channel_obj.id,
            "entity_type": "text_channel",
            "name": new_channel_obj.name,
            "parent_id": parent_category.id,
            "permissions": "read_only",
            "description": "Статья из Библиотеки Знаний.",
            "access_code": None
        }
        
        logger.info(f"Синхронизация нового канала '{channel_name}' с бэкендом...")
        
        # 🔥 ИЗМЕНЕНИЕ: Используем RequestHelper для синхронизации
        discord_context = {
            "user_id": self.bot.user.id, # ID бота
            "guild_id": guild_id,
            "channel_id": new_channel_obj.id, # ID созданного канала
            "command_source": "add_article_channel"
        }
        try:
            response, retrieved_context = await self.request_helper.send_and_await_response(
                api_call=self.bot.http_manager.discord.sync_entities,
                request_model_type=UnifiedEntitySyncRequest,
                request_payload_data={
                    "guild_id": guild_id,
                    "entities_data": [entity_data] # Отправляем список из одного элемента
                },
                discord_context=discord_context
            )

            if response and response.get("success"):
                logger.success(f"Канал '{channel_name}' успешно синхронизирован с бэкендом.")
                return {"status": "success", "message": "Канал-статья успешно создан и синхронизирован."}
            else:
                error_msg = response.get('message') if response else "Нет ответа от сервера"
                logger.error(f"Получен ответ с ошибкой, контекст: {retrieved_context}")
                raise RuntimeError(f"Бэкенд вернул ошибку при синхронизации: {error_msg}")

        except Exception as e:
            logger.error(f"Критическая ошибка при синхронизации канала '{channel_name}': {e}", exc_info=True)
            # Откат: удаляем созданный канал, если синхронизация не удалась
            logger.warning(f"Откат: удаление канала '{channel_name}' из Discord из-за ошибки синхронизации.")
            await self.base_ops.delete_discord_entity(new_channel_obj)
            raise RuntimeError(f"Не удалось сохранить канал в базе данных: {e}")