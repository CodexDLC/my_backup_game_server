# --- Файл: app/services/lobby/presentation_handlers/display_character_selection.py ---

import inject
import discord
import logging # 🔥 НОВОЕ: Импортируем logging
from typing import Union


from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager
from game_server.app_discord_bot.app.ui.views.authentication.character_selection_view import CharacterSelectionView, NoCharactersView
from game_server.app_discord_bot.core.contracts.handler_response_dto import CharacterSelectionDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

class DisplayCharacterSelectionPresenter:
    """
    Отображает экран выбора персонажа, редактируя нижнее сообщение.
    Отправляет итог операции в канал дашборда.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client,
        account_data_manager: IAccountDataManager,
        interaction_response_manager: InteractionResponseManager,
        logger: logging.Logger, # 🔥 НОВОЕ: Инжектируем логгер
    ):
        self.bot = bot
        self.account_data_manager = account_data_manager
        self.interaction_response_manager = interaction_response_manager
        self.logger = logger # 🔥 НОВОЕ: Сохраняем логгер


    async def execute(self, response_dto: CharacterSelectionDTO, interaction: discord.Interaction, helpers, response_message_object: discord.Message | None = None):
        user = interaction.user
        guild = interaction.guild

        view_to_show: Union[CharacterSelectionView, NoCharactersView]
        if response_dto.characters:
            view_to_show = CharacterSelectionView(author=user, characters=response_dto.characters)
        else:
            view_to_show = NoCharactersView(author=user)
        embed_to_show = view_to_show.create_embed()

        try:
            # 1. Получаем ID сообщений и каналов из Redis
            message_ids_data = await self.account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_MESSAGES)
            footer_msg_id = int(message_ids_data["footer_id"])

            channels_data = await self.account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_DISCORD_CHANNELS)
            interface_channel_id = int(channels_data["interface_channel_id"])
            dashboard_channel_id = int(channels_data["dashboard_channel_id"])

            interface_channel = guild.get_channel(interface_channel_id)
            dashboard_channel = guild.get_channel(dashboard_channel_id) or await self.bot.fetch_channel(dashboard_channel_id)

            # 2. Редактируем основное сообщение интерфейса
            footer_msg = await interface_channel.fetch_message(footer_msg_id)
            await footer_msg.edit(embed=embed_to_show, view=view_to_show)

            # 3. Отправляем итог операции в канал дашборда
            if isinstance(dashboard_channel, discord.TextChannel):
                dashboard_embed = discord.Embed(
                    title="📝 Отчет по выбору персонажей",
                    description=f"Пользователь {user.mention} обновил свой список персонажей. "
                                f"Всего персонажей: **{len(response_dto.characters) if response_dto.characters else 0}**.",
                    color=discord.Color.green()
                )
                
                await dashboard_channel.send(embed=dashboard_embed)
                self.logger.info(f"Отчет о выборе персонажей отправлен в дашборд для {user.name} (Канал: {dashboard_channel.name}).") # 🔥 ИЗМЕНЕНИЕ
            else:
                self.logger.warning(f"Канал дашборда для {user.name} (ID: {dashboard_channel_id}) не является текстовым каналом или не найден.") # 🔥 ИЗМЕНЕНИЕ

            # 4. Удаляем кастомное сообщение-индикатор из интерфейсного канала
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object)

        except discord.NotFound:
            await self.interaction_response_manager.send_personal_notification_message(
                interaction,
                "Не удалось найти сообщение для обновления. Попробуйте войти в игру заново.",
                delete_after=None
            )
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
        except Exception as e:
            self.logger.error(f"Произошла ошибка в DisplayCharacterSelectionPresenter для {user.name}: {e}", exc_info=True) # 🔥 ИЗМЕНЕНИЕ
            await self.interaction_response_manager.send_personal_notification_message(
                interaction,
                f"Произошла ошибка при обновлении контента: {e}",
                delete_after=None
            )
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)