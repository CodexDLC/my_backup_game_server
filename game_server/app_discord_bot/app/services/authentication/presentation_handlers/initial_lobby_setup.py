import inject
import discord
import logging
import json
import uuid # Импортируем uuid для генерации уникального ID

from discord.ext import commands
from typing import Union

from game_server.app_discord_bot.app.constant.roles_blueprint import OFFLINE_ROLE, ONLINE_ROLE
from game_server.app_discord_bot.app.services.utils.role_finder import RoleFinder
from game_server.app_discord_bot.app.ui.views.authentication.character_selection_view import CharacterSelectionView, NoCharactersView
from game_server.app_discord_bot.app.ui.views.authentication.lobby_view import LobbyView
from game_server.app_discord_bot.core.contracts.handler_response_dto import InitialLobbySetupDTO
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager


class InitialLobbySetupPresenter:
    """
    Презентационный обработчик для первоначальной отрисовки интерфейса лобби.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        account_data_manager: IAccountDataManager,
        role_finder: RoleFinder,
        interaction_response_manager: InteractionResponseManager,
        logger: logging.Logger,
    ):
        self.bot = bot
        self.account_data_manager = account_data_manager
        self.role_finder = role_finder
        self.interaction_response_manager = interaction_response_manager
        self.logger = logger

    async def execute(self, response_dto: InitialLobbySetupDTO, interaction: discord.Interaction, helpers, response_message_object: discord.Message | None = None):
        user = interaction.user
        guild = interaction.guild

        self.logger.debug(f"DEBUG: InitialLobbySetupPresenter.execute вызван для {user.name}.")
        self.logger.debug(f"DEBUG: response_dto.characters содержит {len(response_dto.characters) if response_dto.characters else 0} персонажей.")
        if response_dto.characters:
            self.logger.debug(f"DEBUG: Персонажи в response_dto: {[char.name for char in response_dto.characters]}")
        else:
            self.logger.debug("DEBUG: response_dto.characters пуст.")

        try:
            channels_data = await self.account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_DISCORD_CHANNELS)
            interface_channel_id = int(channels_data["interface_channel_id"])
            dashboard_channel_id = int(channels_data["dashboard_channel_id"])

            interface_channel = guild.get_channel(interface_channel_id) or await self.bot.fetch_channel(interface_channel_id)
            dashboard_channel = guild.get_channel(dashboard_channel_id) or await self.bot.fetch_channel(dashboard_channel_id)

            message_ids_data = await self.account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_MESSAGES)

            # 1. Меняем роли (ПЕРЕМЕЩЕНО СЮДА)
            # Это происходит до обновления сообщений, чтобы роли были актуальны
            # к моменту, когда пользователь увидит обновленный интерфейс.
            roles_data = await self.account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_DISCORD_ROLES)
            personal_role_id = int(roles_data["personal_role_id"])
            offline_role = await self.role_finder.get_system_role(guild, OFFLINE_ROLE, shard_type="game")
            online_role = await self.role_finder.get_system_role(guild, ONLINE_ROLE, shard_type="game")
            personal_role = guild.get_role(personal_role_id)
            if offline_role: await user.remove_roles(offline_role, reason="Вход на шард")
            if online_role and personal_role: await user.add_roles(online_role, personal_role, reason="Вход на шард")
            self.logger.info(f"Роли пользователя {user.name} обновлены: удалена {OFFLINE_ROLE}, добавлены {ONLINE_ROLE}, {personal_role.name}.")

            # Генерируем уникальный ID для обновления сообщений
            unique_message_id = str(uuid.uuid4())[:8]
            
            # 2. Формируем и отправляем/редактируем верхнее сообщение (Панель интерфейса)
            view_for_top_msg = LobbyView(author=user)
            top_embed = view_for_top_msg.create_embed()
            
            top_msg_id = message_ids_data.get("top_id") if message_ids_data else None
            top_msg = None
            if top_msg_id:
                try:
                    top_msg = await interface_channel.fetch_message(int(top_msg_id))
                    # Добавляем уникальный контент для принудительного обновления
                    await top_msg.edit(content=f"Обновление {unique_message_id}", embed=top_embed, view=view_for_top_msg)
                    self.logger.debug(f"Сообщение интерфейса TOP (ID: {top_msg.id}) успешно отредактировано.")
                except discord.NotFound:
                    top_msg = await interface_channel.send(content=f"Обновление {unique_message_id}", embed=top_embed, view=view_for_top_msg)
                    self.logger.debug(f"Сообщение интерфейса TOP (ID: {top_msg.id}) успешно отправлено (старое не найдено).")
                except Exception as e:
                    self.logger.error(f"Ошибка при редактировании/отправке сообщения интерфейса TOP (ID: {top_msg_id}): {e}", exc_info=True)
                    top_msg = await interface_channel.send(content=f"Обновление {unique_message_id}", embed=top_embed, view=view_for_top_msg)
                    self.logger.debug(f"Сообщение интерфейса TOP (ID: {top_msg.id}) отправлено после ошибки редактирования.")
            else:
                top_msg = await interface_channel.send(content=f"Обновление {unique_message_id}", embed=top_embed, view=view_for_top_msg)
                self.logger.debug(f"Сообщение интерфейса TOP (ID: {top_msg.id}) успешно отправлено (новое).")
                
            # 3. Формируем и отправляем/редактируем нижнее сообщение (Область контента)
            footer_view: Union[CharacterSelectionView, NoCharactersView]
            if response_dto.characters:
                self.logger.debug("DEBUG: Создается CharacterSelectionView.")
                footer_view = CharacterSelectionView(author=user, characters=response_dto.characters)
            else:
                self.logger.debug("DEBUG: Создается NoCharactersView.")
                footer_view = NoCharactersView(author=user)
            footer_embed = footer_view.create_embed()

            footer_msg_id = message_ids_data.get("footer_id") if message_ids_data else None
            footer_msg = None
            
            self.logger.debug(f"DEBUG: Попытка отправить/отредактировать нижнее сообщение с view типа {type(footer_view).__name__}.")
            if footer_msg_id:
                try:
                    footer_msg = await interface_channel.fetch_message(int(footer_msg_id))
                    await footer_msg.delete() # ИЗМЕНЕНО: Удаляем старое сообщение
                    self.logger.debug(f"Сообщение интерфейса FOOTER (ID: {footer_msg.id}) успешно удалено.") # НОВЫЙ ЛОГ
                except discord.NotFound:
                    self.logger.debug(f"Старое сообщение интерфейса FOOTER (ID: {footer_msg_id}) не найдено для удаления.") # НОВЫЙ ЛОГ
                except Exception as e:
                    self.logger.error(f"Ошибка при удалении старого сообщения интерфейса FOOTER (ID: {footer_msg_id}): {e}", exc_info=True)
            
            # Всегда отправляем новое сообщение после возможного удаления старого
            # Добавляем уникальный контент для принудительного обновления
            footer_msg = await interface_channel.send(content=f"Обновление {unique_message_id}", embed=footer_embed, view=footer_view)
            self.logger.debug(f"Сообщение интерфейса FOOTER (ID: {footer_msg.id}) успешно отправлено (новое).") # ИЗМЕНЕНО на DEBUG

            # 4. Сохраняем ID сообщений в Redis
            await self.account_data_manager.save_account_field(
                shard_id=guild.id, discord_user_id=user.id,
                field_name=RedisKeys.FIELD_MESSAGES,
                data={"top_id": str(top_msg.id), "footer_id": str(footer_msg.id)}
            )
            self.logger.info(f"ID сообщений интерфейса сохранены для {user.name}: top_id={top_msg.id}, footer_id={footer_msg.id}.")

            # 5. Отправляем итог операции в канал дашборда
            if isinstance(dashboard_channel, discord.TextChannel):
                dashboard_embed = discord.Embed(
                    title="🚀 Вход в лобби",
                    description=f"Пользователь {user.mention} успешно вошел в игру и его интерфейс готов в канале {interface_channel.mention}.",
                    color=discord.Color.green()
                )
                await dashboard_channel.send(embed=dashboard_embed)
                self.logger.info(f"Отчет о входе в лобби отправлен в дашборд для {user.name} (Канал: {dashboard_channel.name}).")
            else:
                self.logger.warning(f"Канал дашборда для {user.name} (ID: {dashboard_channel_id}) не является текстовым каналом или не найден.")

            # 6. Удаляем кастомное сообщение-индикатор (бывшее 7)
            # Финальное эфемерное сообщение о входе удалено по вашему запросу.
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object)
            self.logger.info(f"Сообщение-индикатор удалено для {user.name}.")

        except Exception as e:
            self.logger.error(f"Произошла критическая ошибка в InitialLobbySetupPresenter для {user.name}: {e}", exc_info=True)
            await self.interaction_response_manager.send_personal_notification_message(
                interaction,
                f"Произошла ошибка при настройке лобби: {e}",
                delete_after=None
            )
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
