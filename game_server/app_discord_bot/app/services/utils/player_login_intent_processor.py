# game_server/app_discord_bot/app/services/utils/player_login_intent_processor.py
import asyncio
import uuid
import discord
import logging
import inject
from typing import Tuple, Union

from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager

from game_server.app_discord_bot.app.constant.constants_world import HUB_GUILD_ID
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
# 🔥 НОВОЕ: Импортируем PlayerEventsHandler, так как он будет вызываться здесь
from game_server.app_discord_bot.app.events.player_events_handler import PlayerEventsHandler
from game_server.contracts.api_models.system.requests import HubRoutingRequest
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload


class PlayerLoginIntentProcessor:
    """
    Процессор намерения логина игрока.
    Определяет, может ли игрок быть залогинен на текущем шарде.
    """
    @inject.autoparams()
    def __init__(
        self,
        account_data_manager: AccountDataManager,
        base_ops: BaseDiscordOperations,
        guild_config_manager: GuildConfigManager,
        request_helper: RequestHelper,
        logger: logging.Logger,
        # 🔥 НОВОЕ: Добавляем PlayerEventsHandler в конструктор
        player_events_handler: PlayerEventsHandler
    ):
        self.account_data_manager = account_data_manager
        self.base_ops = base_ops
        self.guild_config_manager = guild_config_manager
        self.request_helper = request_helper
        self.logger = logger
        # 🔥 НОВОЕ: Сохраняем PlayerEventsHandler как атрибут класса
        self.player_events_handler = player_events_handler
        self.logger.info("✨ PlayerLoginIntentProcessor инициализирован.")

    async def process_login_intent(self, interaction: discord.Interaction) -> bool:
        """
        Основной метод обработки намерения логина.
        Возвращает True, если игрок может быть залогинен на текущем шарде.
        Возвращает False, если произошла ошибка или игрок был перенаправлен.
        """
        user = interaction.user
        guild = interaction.guild
        current_shard_id = guild.id

        self.logger.info(f"[LoginProcessor] Пользователь {user.id} инициировал логин на шарде {current_shard_id}.")
        
        # Отправляем первое информационное сообщение
        await interaction.followup.send("⏳ Ваш запрос на вход обрабатывается...", ephemeral=True)


        try:
            # Шаг 1: Проверка наличия данных в Redis
            roles_data = await self.account_data_manager.get_account_field(
                shard_id=current_shard_id,
                discord_user_id=user.id,
                field_name="discord_roles"
            )
            channels_data = await self.account_data_manager.get_account_field(
                shard_id=current_shard_id,
                discord_user_id=user.id,
                field_name="discord_channels"
            )

            if roles_data and channels_data:
                self.logger.info(f"[LoginProcessor] Обнаружена существующая привязка для {user.id} (поля discord_roles и discord_channels). запускаем логику дальше возвращая True.")
                
                return True
            else:
                self.logger.warning(f"[LoginProcessor] Привязка для {user.id} не найдена или неполная. Запрашиваю данные у бэкенда.")
                # _handle_backend_resolution теперь сам вызывает handle_player_join в случае успеха
                return await self._handle_backend_resolution(interaction, user, guild, current_shard_id)

        except Exception as e:
            self.logger.critical(f"[LoginProcessor] Критическая ошибка в процессе обработки намерения логина для {user.id}: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.followup.send("❌ Произошла критическая ошибка при входе. Пожалуйста, попробуйте позже.", ephemeral=True)
            return False

    async def _handle_backend_resolution(
        self, interaction: discord.Interaction, user: Union[discord.User, discord.Member],
        guild: discord.Guild, current_shard_id: int
    ) -> bool:
        """
        Вспомогательный метод для обращения к бэкенду и обработки его ответа.
        """
        try:
            correlation_id_obj = uuid.uuid4()
            request_payload = HubRoutingRequest(
                correlation_id=str(correlation_id_obj),
                discord_user_id=str(user.id),
                guild_id=str(HUB_GUILD_ID),
            )

            discord_context = {
                "discord_user_id": str(user.id),
                "guild_id": str(guild.id),
                "command_source": "process_login_intent"
            }

            self.logger.info(f"[LoginProcessor] Запрос на разрешение логина для {user.id} отправлен через RequestHelper...")
            
            # Вызываем хелпер
            raw_payload_dict, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.auth.hub_login,
                request_payload=request_payload,
                correlation_id=correlation_id_obj,
                discord_context=discord_context
            )
            
            response_payload = WebSocketResponsePayload(**raw_payload_dict)

            if response_payload.status.upper() != "SUCCESS":
                error_msg = response_payload.error.message if response_payload.error else "Неизвестная ошибка от сервера."
                raise RuntimeError(error_msg)

            backend_resolved_shard_id = response_payload.data.get("shard_id")
            account_id = response_payload.data.get("account_id") # Получаем account_id из ответа бэкенда

            if backend_resolved_shard_id is None or account_id is None:
                self.logger.error(f"[LoginProcessor] Бэкенд вернул SUCCESS, но данные неполные: {response_payload.data}")
                raise RuntimeError("Неполные данные от бэкенда при разрешении логина.")


            if int(backend_resolved_shard_id) == current_shard_id:
                self.logger.info(f"[LoginProcessor] Бэкенд подтвердил привязку к текущему шарду {current_shard_id}. Запускаю пост-логин настройку.")
                
                # 🔥 НОВОЕ: Сохраняем account_id в Redis здесь, так как он нужен для handle_player_join
                await self.account_data_manager.set_discord_account_mapping(
                    discord_user_id=user.id,
                    account_id=int(account_id)
                )
                self.logger.debug(f"[LoginProcessor] Сохранено глобальное сопоставление Discord ID {user.id} -> Account ID {account_id}.")

                # 🔥 НОВОЕ: Вызываем handle_player_join для запуска следующего этапа настройки
                await self.player_events_handler.handle_player_join(user)
                return True
            else:
                self.logger.info(f"[LoginProcessor] Бэкенд перенаправил {user.id} на другой шард: {backend_resolved_shard_id}.")
                await self._redirect_player(interaction, user, guild, int(backend_resolved_shard_id))
                return False

        except (RuntimeError, asyncio.TimeoutError) as e:
            self.logger.error(f"[LoginProcessor] Ошибка при обращении к бэкенду для {user.id}: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Ошибка при связи с сервером: {e}", ephemeral=True)
            return False
        except Exception as e:
            self.logger.critical(f"[LoginProcessor] Ошибка в процессе разрешения логина через бэкенд для {user.id}: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Критическая ошибка при связи с сервером: {e}", ephemeral=True)
            return False

    async def _redirect_player(self, interaction: discord.Interaction, user: discord.Member, current_guild: discord.Guild, target_shard_id: int):
        """Перенаправляет игрока на другой шард."""
        target_guild = await self.base_ops.get_guild_by_id(target_shard_id)
        if not target_guild:
            raise RuntimeError(f"Не удалось найти целевой шард-сервер с ID: {target_shard_id}")

        layout_config = await self.guild_config_manager.get_field(target_guild.id, "layout_config", "game")
        if not layout_config:
            raise RuntimeError(f"Конфигурация для целевого шарда {target_guild.id} не найдена.")

        reception_channel_id_str = layout_config.get("layout_structure", {}).get("categories", {}).get("Category: GENERAL_CHANNELS", {}).get("channels", {}).get("reception", {}).get("discord_id")
        if not reception_channel_id_str:
            raise RuntimeError(f"Не найден канал 'reception' в конфигурации целевого шарда.")

        welcome_channel = target_guild.get_channel(int(reception_channel_id_str))
        if not welcome_channel or not isinstance(welcome_channel, discord.TextChannel):
            raise RuntimeError(f"Канал 'reception' (ID: {reception_channel_id_str}) не найден на целевом шарде.")

        invite_link = await self.base_ops.create_invite_link(welcome_channel)
        if not invite_link:
            raise RuntimeError("Не удалось создать ссылку-приглашение.")

        await self.base_ops.send_dm_message(user, f"Ваш игровой аккаунт привязан к другому миру. Пожалуйста, перейдите по этой ссылке: {invite_link}")
        await interaction.followup.send("✅ Вы были перенаправлены на другой игровой мир. Проверьте личные сообщения.", ephemeral=True)
        await current_guild.kick(user, reason=f"Перенаправление на шард {target_shard_id}.")
