# game_server/app_discord_bot/app/services/admin/article_management_service.py

from typing import Dict, Any, Optional, List
import discord
from discord import TextChannel, utils
import uuid
import logging # <-- Добавлено для типизации
import inject # <-- Добавлено для inject.autoparams

from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper

from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntitySyncRequest
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload


class ArticleManagementService:
    """
    Сервисный слой для управления каналами-статьями.
    Создает канал в Discord и отправляет его на бэкенд для синхронизации.
    """
    # 🔥 ИЗМЕНЕНИЕ: bot теперь прямой аргумент, не инжектируется через autoparams
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client, # <-- bot теперь такая же зависимость, как и все остальные
        base_ops: BaseDiscordOperations,
        request_helper: RequestHelper,
        logger: logging.Logger
    ):
        self.bot = bot
        self.base_ops = base_ops
        self.channels_config = CHANNELS_CONFIG
        self.request_helper = request_helper
        self.logger = logger
        self.bot = bot # <--- Сохраняем переданный экземпляр бота


    async def add_article_channel(self, guild_id: int, channel_name: str) -> Dict[str, Any]:
        """
        Добавляет новый текстовый канал-статью и синхронизирует его с бэкендом.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord server with ID {guild_id} not found.")
        
        knowledge_category_name = next(
            (cat_name for cat_name in self.channels_config.get("hub_layout", {})
             if "БИБЛИОТЕКА ЗНАНИЙ" in cat_name),
            "Категория: [ БИБЛИОТЕКА ЗНАНИЙ ] 📚"
        )

        self.logger.info(f"Попытка добавить канал '{channel_name}' в категорию '{knowledge_category_name}'.")
        parent_category = utils.get(guild.categories, name=knowledge_category_name)
        if not parent_category:
            raise ValueError(f"Категория '{knowledge_category_name}' не найдена на сервере.")

        new_channel_obj: Optional[TextChannel] = None
        try:
            new_channel_obj = await self.base_ops.create_discord_channel(
                guild, channel_name, "text", parent_category=parent_category,
                permissions="read_only", description="Статья из Библиотеки Знаний."
            )
            if not new_channel_obj:
                raise RuntimeError("Не удалось создать канал в Discord, объект не был возвращен.")
            self.logger.success(f"Канал '{channel_name}' успешно создан в Discord (ID: {new_channel_obj.id}).")
        except Exception as e:
            self.logger.error(f"Ошибка при создании канала '{channel_name}' в Discord: {e}", exc_info=True)
            raise ValueError(f"Не удалось создать канал в Discord: {e}")

        entity_data = {
            "discord_id": new_channel_obj.id,
            "entity_type": "text_channel",
            "name": new_channel_obj.name,
            "parent_id": parent_category.id,
            "permissions": "read_only",
            "description": "Статья из Библиотеки Знаний.",
            "access_code": None
        }
        
        self.logger.info(f"Синхронизация нового канала '{channel_name}' с бэкендом...")
        
        discord_context = {
            "user_id": self.bot.user.id,
            "guild_id": guild_id,
            "channel_id": new_channel_obj.id,
            "command_source": "add_article_channel"
        }
        try:
            raw_ws_dict, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_entities,
                request_model_type=UnifiedEntitySyncRequest,
                request_payload_data={
                    "guild_id": guild_id,
                    "entities_data": [entity_data]
                },
                discord_context=discord_context
            )
            
            full_message = WebSocketMessage(**raw_ws_dict)
            response_payload = WebSocketResponsePayload(**full_message.payload)

            if response_payload.status == ResponseStatus.SUCCESS:
                self.logger.success(f"Канал '{channel_name}' успешно синхронизирован с бэкендом.")
                return {"status": "success", "message": "Канал-статья успешно создан и синхронизирован."}
            else:
                error_msg = response_payload.error.message if response_payload.error else "Бэкенд вернул ошибку при синхронизации."
                raise RuntimeError(error_msg)

        except Exception as e:
            self.logger.error(f"Критическая ошибка при синхронизации канала '{channel_name}': {e}", exc_info=True)
            self.logger.warning(f"Откат: удаление канала '{channel_name}' из Discord из-за ошибки синхронизации.")
            await self.base_ops.delete_discord_entity(new_channel_obj)
            raise RuntimeError(f"Не удалось сохранить канал в базе данных: {e}")