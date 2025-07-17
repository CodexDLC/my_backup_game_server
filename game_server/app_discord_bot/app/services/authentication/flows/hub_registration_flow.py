# game_server/app_discord_bot/app/services/authentication/flows/hub_registration_flow.py
# Version: 0.006 # Версия увеличена на 0.001

import asyncio
import uuid
import discord
import json
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

# Импорты для работы с Redis конфигом гильдии
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
# Импорт RedisKeys
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
# Импорт основного логгера приложения
from game_server.config.logging.logging_setup import app_logger as logger

# Импорты контрактов API

from game_server.contracts.api_models.system.requests import HubRoutingRequest
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload


# Импорты сервисов
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
# Добавляем импорт RequestHelper
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
# НОВОЕ: Импортируем декоратор для обработки ошибок
from game_server.app_discord_bot.app.services.utils.error_handlers import handle_flow_errors


@handle_flow_errors # Применяем декоратор для централизованной обработки ошибок
async def execute_hub_registration_flow(
    interaction: discord.Interaction,
    bot: discord.Client,
    account_data_manager: AccountDataManager,
    base_ops: BaseDiscordOperations,
    guild_config_manager: GuildConfigManager,
    request_helper: RequestHelper
) -> None:
    user = interaction.user
    logger.info(f"Запуск процесса регистрации для пользователя: {user.name} ({user.id})")

    correlation_id_obj = uuid.uuid4()
    request_payload = HubRoutingRequest(
        correlation_id=str(correlation_id_obj),
        discord_user_id=str(user.id),
        guild_id=str(interaction.guild.id),
    )

    discord_context = {
        "discord_user_id": str(user.id),
        "guild_id": str(interaction.guild.id),
        "command_source": "execute_hub_registration_flow"
        # ИСПРАВЛЕНО: client_id удален из discord_context, т.к. он добавляется RequestHelper
    }

    logger.info(f"Запрос на регистрацию для {user.id} успешно отправлен через RequestHelper. Ожидаем WebSocket-ответ...")
    
    # raw_websocket_message_dict здесь - это полная WebSocketMessage (как словарь), возвращаемая RequestHelper
    raw_websocket_message_dict, _ = await request_helper.send_and_await_response(
        api_method=request_helper.http_client_gateway.auth.hub_login,
        request_payload=request_payload,
        correlation_id=correlation_id_obj,
        discord_context=discord_context
    )
    
    # ИСПРАВЛЕНИЕ: Сначала валидируем весь WebSocketMessage
    full_ws_message = WebSocketMessage(**raw_websocket_message_dict)

    # ИСПРАВЛЕНИЕ: Теперь извлекаем payload и валидируем его как WebSocketResponsePayload
    response_payload = WebSocketResponsePayload(**full_ws_message.payload)
    
    logger.debug(f"Получены данные ответа от сервера: {response_payload.data}")


    if response_payload.status.upper() != "SUCCESS":
        error_msg = response_payload.error.message if response_payload.error else "Неизвестная ошибка от сервера."
        raise RuntimeError(error_msg)

    account_id = response_payload.data.get("account_id")
    shard_id = response_payload.data.get("shard_id")

    if not account_id or not shard_id:
        raise RuntimeError("Сервер вернул неполные данные (account_id или shard_id отсутствуют).")

    shard_guild = await base_ops.get_guild_by_id(int(shard_id))
    if not shard_guild:
        raise RuntimeError(f"Не удалось найти целевой шард-сервер с ID: {shard_id}")

    layout_config = await guild_config_manager.get_field(
        guild_id=int(shard_id),
        shard_type="game",
        field_name=RedisKeys.FIELD_LAYOUT_CONFIG
    )

    if not layout_config:
        logger.warning(f"Конфигурация лейаута для шарда {shard_guild.id} не найдена в Redis. Возможно, шард не развернут.")
        raise RuntimeError(f"Игровой мир {shard_guild.id} временно недоступен или еще не готов. Пожалуйста, попробуйте позже.")


    reception_channel_id = None
    try:
        reception_channel_id = int(layout_config \
                                    .get("layout_structure", {}) \
                                    .get("categories", {}) \
                                    .get("Category: GENERAL_CHANNELS", {}) \
                                    .get("channels", {}) \
                                    .get("reception", {}) \
                                    .get("discord_id"))
    except (AttributeError, TypeError, ValueError) as e:
        logger.error(f"Ошибка при парсинге layout_config для reception_channel_id на шарде {shard_guild.id}: {e}", exc_info=True)
        reception_channel_id = None

    if not reception_channel_id:
        raise RuntimeError(f"Не удалось найти 'discord_id' для канала 'reception' в конфигурации шарда {shard_guild.id}.")

    welcome_channel = shard_guild.get_channel(reception_channel_id)

    if not welcome_channel or not isinstance(welcome_channel, discord.TextChannel):
        raise RuntimeError(f"Канал 'reception' (ID: {reception_channel_id}) не найден или не является текстовым каналом.")

    invite_link = await base_ops.create_invite_link(welcome_channel)
    if not invite_link:
        raise RuntimeError("Не удалось создать ссылку-приглашение.")

    current_time = datetime.now().isoformat()
    
    await account_data_manager.set_discord_account_mapping(
        discord_user_id=int(user.id),
        account_id=int(account_id)
    )
    logger.debug(f"Сохранено глобальное сопоставление Discord ID {user.id} -> Account ID {account_id}.")

    await account_data_manager.save_account_field(
        shard_id=int(shard_id),
        discord_user_id=int(user.id),
        field_name=RedisKeys.FIELD_ACCOUNT_ID,
        data=str(account_id)
    )
    logger.debug(f"Account ID {account_id} сохранен как поле в данных Discord пользователя {user.id} на шарде {shard_id}.")

    general_info_data = {
        "registered_from_hub_id": str(interaction.guild.id),
        "created_at": current_time
    }
    await account_data_manager.save_account_field(
        shard_id=int(shard_id),
        discord_user_id=int(user.id),
        field_name=RedisKeys.FIELD_GENERAL_INFO,
        data=general_info_data
    )

    linked_discord_meta_data = {
        "player_role_id": None,
        "invite_link": invite_link,
        "welcome_channel_id": str(welcome_channel.id)
    }
    await account_data_manager.save_account_field(
        shard_id=int(shard_id),
        discord_user_id=int(user.id),
        field_name=RedisKeys.FIELD_LINKED_DISCORD_META,
        data=linked_discord_meta_data
    )

    logger.info(f"Данные аккаунта {account_id} (Discord ID: {user.id}) успешно сохранены в Redis на шарде {shard_id} по новой структуре.")

    # ========================================================================================
    # НОВОЕ: АТОМАРНОЕ добавление Discord ID пользователя в список зарегистрированных игроков на шарде
    # ========================================================================================
    try:
        await guild_config_manager.add_player_id_to_registered_list(
            guild_id=int(shard_id), # Здесь guild_id - это ID шарда
            shard_type="game",
            player_discord_id=str(user.id)
        )
        logger.info(f"Discord ID {user.id} атомарно добавлен в список зарегистрированных игроков на шарде {shard_id}.")

    except Exception as e:
        logger.error(f"Ошибка при атомарном добавлении Discord ID {user.id} в список зарегистрированных игроков на шарде {shard_id}: {e}", exc_info=True)
        # Эта ошибка не должна прерывать процесс регистрации игрока, но должна быть залогирована.
        # Поскольку декоратор handle_flow_errors перехватывает Exception, мы не перевыбрасываем здесь.

    await interaction.edit_original_response(content="✅ Готово! Ссылка-приглашение отправлена вам личным сообщением в этом канале.")
    await interaction.followup.send(f"Ваш игровой мир готов. Ссылка для входа: {invite_link}", ephemeral=True)

    # Блоки except в конце функции УДАЛЕНЫ, так как их функциональность берет на себя декоратор @handle_flow_errors.