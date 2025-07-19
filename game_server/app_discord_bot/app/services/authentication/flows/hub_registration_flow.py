import uuid
import discord
from datetime import datetime
# Удаляем импорт RegistrationResultDTO, так как он больше не нужен
from game_server.config.logging.logging_setup import app_logger as logger

# Импорты зависимостей (остаются)
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
from game_server.app_discord_bot.app.services.utils.error_handlers import handle_flow_errors
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager

# Импорты контрактов (остаются)

from game_server.contracts.dtos.auth.commands import HubRoutingPayload, HubRoutingRequest
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload


@handle_flow_errors
async def execute_hub_registration_flow(
    interaction: discord.Interaction,
    # bot: discord.Client, # Этот параметр больше не нужен
    account_data_manager: AccountDataManager,
    base_ops: BaseDiscordOperations,
    guild_config_manager: GuildConfigManager,
    ws_manager: WebSocketManager
) -> None: # Тип возвращаемого значения теперь None
    user = interaction.user
    logger.info(f"Запуск процесса регистрации для пользователя: {user.name} ({user.id})")

    # --- 1. Формирование и отправка команды через WebSocket ---
    payload_data = HubRoutingPayload(
        discord_user_id=str(user.id),
        guild_id=str(interaction.guild.id),
        command="discord_hub_registered" # Явно указываем здесь, если оно не Literal
    )

    # Давайте предположим, что request_data.command по-прежнему нужен, и HubRoutingRequest его содержит.
    request_data = HubRoutingRequest(
        command=payload_data.command, # Берем команду из payload_data, если она там есть
        payload=payload_data # Передаем объект Payload, а не его model_dump()
    )

    logger.info(f"Отправка WebSocket-команды '{request_data.command}' для {user.id}...")
    
    raw_websocket_message_dict, _ = await ws_manager.send_command(
        command_type=request_data.command,
        command_payload=request_data.model_dump(), # Теперь это будет {'command': 'discord_hub_registered', 'payload': {...}}
        domain="auth",
        discord_context={"user_id": str(user.id), "guild_id": str(interaction.guild.id)}
    )
    
    # --- 2. Обработка ответа от бэкенда ---
    full_ws_message = WebSocketMessage(**raw_websocket_message_dict)
    response_payload = WebSocketResponsePayload(**full_ws_message.payload)
    
    logger.debug(f"Получены данные ответа от сервера: {response_payload.data}")

    if response_payload.status.upper() != "SUCCESS":
        error_msg = response_payload.error.message if response_payload.error else "Неизвестная ошибка от сервера."
    
        await interaction.followup.send(f"Произошла ошибка регистрации: {error_msg}", ephemeral=True) # <--- ИСПОЛЬЗУЕМ FOLLOWUP
        raise RuntimeError(error_msg)

    # --- 3. Вся ваша оригинальная логика по работе с данными ---
    account_id = response_payload.data.get("account_id")
    shard_id = response_payload.data.get("shard_id")

    if not account_id or not shard_id:
        error_msg = "Сервер вернул неполные данные (account_id или shard_id отсутствуют)."
        await interaction.followup.send(f"Ошибка: {error_msg}", ephemeral=True) # <--- ИСПРАВЛЕНО
        raise RuntimeError(error_msg)

    shard_guild = await base_ops.get_guild_by_id(int(shard_id))
    if not shard_guild:
        error_msg = f"Не удалось найти целевой шард-сервер с ID: {shard_id}"
        await interaction.followup.send(f"Ошибка: {error_msg}", ephemeral=True) # <--- ИСПРАВЛЕНО
        raise RuntimeError(error_msg)

    layout_config = await guild_config_manager.get_field(
        guild_id=int(shard_id),
        shard_type="game",
        field_name=RedisKeys.FIELD_LAYOUT_CONFIG
    )

    if not layout_config:
        logger.warning(f"Конфигурация лейаута для шарда {shard_guild.id} не найдена в Redis.")
        error_msg = f"Игровой мир {shard_guild.id} временно недоступен или еще не готов."
        await interaction.followup.send(f"Ошибка: {error_msg}", ephemeral=True) # <--- ИСПРАВЛЕНО
        raise RuntimeError(error_msg)

    reception_channel_id = int(layout_config.get("layout_structure", {}).get("categories", {}).get("Category: GENERAL_CHANNELS", {}).get("channels", {}).get("reception", {}).get("discord_id"))

    if not reception_channel_id:
        error_msg = f"Не удалось найти 'discord_id' для канала 'reception' в конфигурации шарда {shard_guild.id}."
        await interaction.followup.send(f"Ошибка: {error_msg}", ephemeral=True) # <--- ИСПРАВЛЕНО
        raise RuntimeError(error_msg)

    welcome_channel = shard_guild.get_channel(reception_channel_id)

    if not welcome_channel or not isinstance(welcome_channel, discord.TextChannel):
        error_msg = f"Канал 'reception' (ID: {reception_channel_id}) не найден или не является текстовым каналом."
        await interaction.followup.send(f"Ошибка: {error_msg}", ephemeral=True) # <--- ИСПРАВЛЕНО
        raise RuntimeError(error_msg)

    invite_link = await base_ops.create_invite_link(welcome_channel)
    if not invite_link:
        error_msg = "Не удалось создать ссылку-приглашение."
        await interaction.followup.send(f"Ошибка: {error_msg}", ephemeral=True) # <--- ИСПРАВЛЕНО
        raise RuntimeError(error_msg)

    current_time = datetime.now().isoformat()
    
    await account_data_manager.set_discord_account_mapping(
        discord_user_id=int(user.id),
        account_id=int(account_id)
    )

    await account_data_manager.save_account_field(
        shard_id=int(shard_id),
        discord_user_id=int(user.id),
        field_name=RedisKeys.FIELD_ACCOUNT_ID,
        data=str(account_id)
    )

    general_info_data = {"registered_from_hub_id": str(interaction.guild.id), "created_at": current_time}
    await account_data_manager.save_account_field(
        shard_id=int(shard_id),
        discord_user_id=int(user.id),
        field_name=RedisKeys.FIELD_GENERAL_INFO,
        data=general_info_data
    )

    linked_discord_meta_data = {"player_role_id": None, "invite_link": invite_link, "welcome_channel_id": str(welcome_channel.id)}
    await account_data_manager.save_account_field(
        shard_id=int(shard_id),
        discord_user_id=int(user.id),
        field_name=RedisKeys.FIELD_LINKED_DISCORD_META,
        data=linked_discord_meta_data
    )
    
    await guild_config_manager.add_player_id_to_registered_list(
        guild_id=int(shard_id),
        shard_type="game",
        player_discord_id=str(user.id)
    )
    
    logger.info(f"Данные аккаунта {account_id} (Discord ID: {user.id}) успешно сохранены в Redis на шарде {shard_id}.")

    # --- 4. Отправляем эфемерное сообщение напрямую ---
    # Public message больше не нужен, формируем сообщение прямо здесь
    final_message = f"✅ Готово! Вы успешно зарегистрированы. Вот ваша ссылка-приглашение: {invite_link}"
    
    # Отправляем эфемерное сообщение туда, откуда была вызвана кнопка
    await interaction.followup.send(final_message, ephemeral=True)
    logger.info(f"Эфемерное сообщение с ссылкой отправлено пользователю {user.name} ({user.id}).")

    return None # Функция теперь ничего не возвращает