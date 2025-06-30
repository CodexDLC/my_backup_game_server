# app/services/authentication/flows/hub_registration_flow.py
import asyncio
import uuid
import discord
from typing import Dict, Any

from game_server.common_contracts.api_models.auth_api import HubRoutingRequest
from game_server.common_contracts.shared_models.api_contracts import WebSocketResponsePayload
from game_server.config.logging.logging_setup import app_logger as logger

from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations


async def execute_hub_registration_flow(
    bot, 
    interaction: discord.Interaction
) -> None:
    """
    Выполняет полный пошаговый процесс регистрации пользователя через Хаб.
    
    Args:
        bot: Экземпляр бота для доступа к менеджерам (ws_manager, http_manager).
        interaction: Исходное взаимодействие от пользователя.
    """
    user = interaction.user
    base_ops = BaseDiscordOperations(bot)
    logger.info(f"Запуск процесса регистрации для пользователя: {user.name} ({user.id})")

    # 2. Готовимся к получению ответа по WebSocket
    correlation_id = uuid.uuid4()
    future = bot.ws_manager.pending_requests.create_request(correlation_id)
    
    # 3. Отправляем инициирующий HTTP-запрос
    request_payload = HubRoutingRequest(
        correlation_id=correlation_id,
        discord_user_id=user.id,
        guild_id=interaction.guild.id,
        avatar=str(user.avatar.url) if user.avatar else None,
        locale=str(interaction.locale)
    )

    try:
        http_response = await bot.http_manager.auth.hub_login(request_payload)
        if not http_response:
            raise RuntimeError("Сервер не принял запрос на регистрацию (HTTP-ответ не был получен).")

        logger.info(f"Запрос на регистрацию для {user.id} успешно отправлен. Ожидаем WebSocket-ответ...")
        
        # 4. Асинхронно ждем ответа по WebSocket
        response_payload: WebSocketResponsePayload = await future

        # 5. Обрабатываем успешный ответ
        if response_payload.status != "SUCCESS":
            error_msg = response_payload.error.message if response_payload.error else "Неизвестная ошибка от сервера."
            raise RuntimeError(error_msg)

        account_id = response_payload.data.get("account_id")
        shard_id = response_payload.data.get("shard_id")

        if not account_id or not shard_id:
            raise RuntimeError("Сервер вернул неполные данные (account_id или shard_id отсутствуют).")

        shard_guild = await base_ops.get_guild_by_id(shard_id)
        if not shard_guild:
            raise RuntimeError(f"Не удалось найти целевой шард-сервер с ID: {shard_id}")

        player_role = await base_ops.create_player_role(shard_guild, account_id)
        if not player_role:
            raise RuntimeError("Не удалось создать роль для игрока на шарде.")
        
        # TODO: Здесь будет вызов API для сохранения роли в DiscordEntity

        welcome_channel = discord.utils.get(shard_guild.text_channels, name="приёмная")
        if not welcome_channel:
             raise RuntimeError("Не удалось найти канал 'приёмная' на целевом шарде.")

        invite_link = await base_ops.create_invite_link(welcome_channel)
        if not invite_link:
            raise RuntimeError("Не удалось создать ссылку-приглашение.")

        await base_ops.send_dm_message(user, f"✅ Регистрация завершена! Ваш игровой мир готов. Ссылка для входа: {invite_link}")
        await interaction.edit_original_response(content="✅ Готово! Проверьте личные сообщения, я отправил вам ссылку-приглашение.")

    except asyncio.TimeoutError:
        logger.error(f"Таймаут ожидания ответа на регистрацию для {user.id}")
        await interaction.edit_original_response(content="❌ Сервер не ответил вовремя. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка в процессе регистрации для {user.id}: {e}", exc_info=True)
        await interaction.edit_original_response(content=f"❌ Произошла критическая ошибка: {e}")
        await base_ops.send_dm_message(user, "При регистрации произошла ошибка. Пожалуйста, свяжитесь с администрацией.")

