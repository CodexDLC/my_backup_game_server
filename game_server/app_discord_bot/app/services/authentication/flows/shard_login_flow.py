# game_server/app_discord_bot/app/services/authentication/flows/shard_login_flow.py
# Version: 0.007

import logging
import inject
import discord
from discord.ext import commands
from typing import Union

# Импорты из других частей проекта
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.app.services.utils.error_handlers import handle_flow_errors
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.app.ui.views.authentication.lobby_view import LobbyView
from game_server.app_discord_bot.app.constant.roles_blueprint import OFFLINE_ROLE, ONLINE_ROLE
from game_server.app_discord_bot.app.services.utils.role_finder import RoleFinder
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

# --- НОВЫЕ И ИЗМЕНЕННЫЕ ИМПОРТЫ ---
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager

from game_server.contracts.dtos.auth.commands import GetSessionDataCommandDTO
from game_server.contracts.dtos.system.results import DiscordShardLoginResponseData
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload
from game_server.app_discord_bot.app.ui.views.authentication.character_selection_view import CharacterSelectionView, NoCharactersView
from game_server.app_discord_bot.app.services.utils.message_sender_service import MessageSenderService


@handle_flow_errors
@inject.autoparams()
async def execute_shard_login_flow(
    interaction: discord.Interaction,
    bot: commands.Bot,
    account_data_manager: IAccountDataManager,
    base_ops: BaseDiscordOperations,
    role_finder: RoleFinder,
    message_sender_service: MessageSenderService,
    ws_manager: WebSocketManager,
):
    user = interaction.user
    guild = interaction.guild
    logger.info(f"[ShardLoginFlow] Запуск для пользователя {user.name} ({user.id}) в гильдии {guild.name} ({guild.id}).")

    # 0. Получение account_id из Redis (логика остается)
    account_id_from_cache_str = await account_data_manager.get_account_id_by_discord_id(user.id)
    if account_id_from_cache_str is None:
        await interaction.followup.send("Ваш игровой аккаунт не найден. Пожалуйста, убедитесь, что вы зарегистрированы.", ephemeral=True)
        return
    try:
        account_id = int(account_id_from_cache_str)
    except ValueError:
        await interaction.followup.send("Произошла ошибка с вашими данными аккаунта. Пожалуйста, свяжитесь с администрацией.", ephemeral=True)
        return

    # 1. Отправка команды через WebSocketManager
    command_dto = GetSessionDataCommandDTO(account_id=account_id)
    
    try:
        # ws_manager.send_command возвращает весь "конверт" WebSocketMessage
        full_message_dict, _ = await ws_manager.send_command(
            command_type=command_dto.command,
            command_payload=command_dto.model_dump(),
            domain="auth",
            discord_context={"user_id": user.id, "guild_id": guild.id}
        )
        logger.info(f"Получен ответ от сервера на команду '{command_dto.command}': {full_message_dict}")

        # 2. Валидация ответа
        # ▼▼▼ ИСПРАВЛЕНИЕ ЗДЕСЬ ▼▼▼
        # Сначала извлекаем вложенный payload из полного сообщения
        response_payload_dict = full_message_dict['payload']
        # Теперь валидируем только его
        ws_response_payload = WebSocketResponsePayload(**response_payload_dict) 
        
        if ws_response_payload.status == ResponseStatus.SUCCESS:
            result_data = DiscordShardLoginResponseData(**ws_response_payload.data) 
            logger.info(f"Команда '{command_dto.command}' успешно выполнена для пользователя {user.id}.")

            # --- ВСЯ ДАЛЬНЕЙШАЯ ЛОГИКА ОСТАЕТСЯ ПРАКТИЧЕСКИ БЕЗ ИЗМЕНЕНИЙ ---
            
            # Получение interface_channel
            channels_data = await account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_DISCORD_CHANNELS)
            interface_channel_id = int(channels_data["interface_channel_id"])
            interface_channel = guild.get_channel(interface_channel_id) or await bot.fetch_channel(interface_channel_id)

            # Обновление сообщений
            message_ids_data = await account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_MESSAGES)
            
            # ... (логика обновления top_msg) ...
            view_for_top_msg = LobbyView(author=user)
            top_embed = view_for_top_msg.create_embed()
            if message_ids_data and message_ids_data.get("top_id"):
                try:
                    top_msg = await interface_channel.fetch_message(int(message_ids_data.get("top_id")))
                    await top_msg.edit(embed=top_embed, view=view_for_top_msg)
                except discord.NotFound:
                     top_msg = await interface_channel.send(embed=top_embed, view=view_for_top_msg)
            else:
                top_msg = await interface_channel.send(embed=top_embed, view=view_for_top_msg)

            # ... (логика формирования footer_msg) ...
            footer_view: Union[CharacterSelectionView, NoCharactersView]
            footer_embed: discord.Embed
            if result_data.characters:
                footer_view = CharacterSelectionView(author=user, characters=result_data.characters)
                footer_embed = footer_view.create_embed()
            else:
                footer_view = NoCharactersView(author=user)
                footer_embed = footer_view.create_embed()

            if not message_ids_data or not message_ids_data.get("footer_id"):
                footer_msg = await interface_channel.send(embed=footer_embed, view=footer_view)
                await account_data_manager.save_account_field(
                    shard_id=guild.id, discord_user_id=user.id,
                    field_name=RedisKeys.FIELD_MESSAGES,
                    data={"top_id": str(top_msg.id), "footer_id": str(footer_msg.id)}
                )
            else:
                await message_sender_service.edit_message_with_view(
                    guild=guild, channel_id=interface_channel.id, message_id=int(message_ids_data.get("footer_id")),
                    embed_title=footer_embed.title, embed_description=footer_embed.description,
                    embed_footer=footer_embed.footer.text if footer_embed.footer else "",
                    view_class=type(footer_view), bot_instance=bot, embed_color=footer_embed.color
                )

            # ... (логика смены ролей) ...
            roles_data = await account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_DISCORD_ROLES)
            personal_role_id = int(roles_data["personal_role_id"])
            offline_role = await role_finder.get_system_role(guild, OFFLINE_ROLE, shard_type="game")
            online_role = await role_finder.get_system_role(guild, ONLINE_ROLE, shard_type="game")
            personal_role = guild.get_role(personal_role_id)
            if offline_role: await user.remove_roles(offline_role, reason="Вход на шард")
            if online_role and personal_role: await user.add_roles(online_role, personal_role, reason="Вход на шард")

            await interaction.followup.send(
                f"Добро пожаловать в игру, {user.mention}! Ваш интерфейс готов в канале {interface_channel.mention}.",
                ephemeral=True
            )

        else: # Если ws_response_payload.status не SUCCESS
            error_message = ws_response_payload.message or "Неизвестная ошибка при запросе данных сессии."
            logger.error(f"Ошибка '{command_dto.command}' для пользователя {user.id}: {error_message}")
            await interaction.followup.send(f"Ошибка при входе в игру: {error_message}", ephemeral=True)

    except ConnectionError as ce:
        logger.error(f"Ошибка соединения в Shard Login Flow: {ce}")
        await interaction.followup.send("Не удалось установить связь с игровым сервером. Пожалуйста, попробуйте позже.", ephemeral=True)
    except Exception as e:
        logger.exception(f"Критическая ошибка в Shard Login Flow для пользователя {user.id}.")
        await interaction.followup.send("Произошла непредвиденная ошибка при входе в игру.", ephemeral=True)
