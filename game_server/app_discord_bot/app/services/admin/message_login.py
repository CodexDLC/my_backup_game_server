# game_server/app_discord_bot/app/services/admin/message_login.py

import discord
import logging
from typing import Dict, Any, Optional, Type

# Импорты, необходимые для этой функции
from game_server.app_discord_bot.app.ui.views.authentication.login_view import LoginView # Теперь импортируется здесь
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.app.ui.messages.authentication.general_login_messages import (
    GENERAL_LOGIN_EMBED_TITLE, GENERAL_LOGIN_EMBED_DESCRIPTION, GENERAL_LOGIN_EMBED_FOOTER
)
from game_server.app_discord_bot.app.services.utils.message_sender_service import MessageSenderService # Импортируем универсальный сервис

# Используем app_logger из централизованного места
from game_server.config.logging.logging_setup import app_logger as logger

async def send_login_message_to_reception_channel(
    guild: discord.Guild,
    layout_config: Dict[str, Any],
    bot: discord.Client,
    message_sender_service: MessageSenderService, # Теперь принимаем MessageSenderService как аргумент
    guild_config_manager: GuildConfigManager, # Теперь принимаем GuildConfigManager как аргумент
) -> Optional[discord.Message]:
    """
    Специфичная функция для отправки сообщения логина в канал 'reception'.
    Использует универсальный метод send_message_with_view из MessageSenderService.
    """
    reception_channel_id = layout_config \
                                .get("layout_structure", {}) \
                                .get("categories", {}) \
                                .get("Category: GENERAL_CHANNELS", {}) \
                                .get("channels", {}) \
                                .get("reception", {}) \
                                .get("discord_id")

    if not reception_channel_id:
        logger.error(f"Не удалось найти 'discord_id' для канала 'reception' в конфигурации гильдии {guild.id}. Сообщение логина не будет отправлено.")
        return None

    # 🔥 ВАЖНО: LoginView теперь импортируется в этом файле и передается
    return await message_sender_service.send_message_with_view(
        guild=guild,
        channel_id=int(reception_channel_id),
        embed_title=GENERAL_LOGIN_EMBED_TITLE,
        embed_description=GENERAL_LOGIN_EMBED_DESCRIPTION,
        embed_footer=GENERAL_LOGIN_EMBED_FOOTER,
        view_class=LoginView, # Передаем сам КЛАСС LoginView
        bot_instance=bot, # Передаем объект бота
        redis_field_name=RedisKeys.FIELD_LOGIN_MESSAGE_ID,
        shard_type="game"
    )
