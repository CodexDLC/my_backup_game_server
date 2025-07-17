# app/services/utils/interaction_response_manager.py

import inject
import discord
import logging
from discord.ext import commands

from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

class InteractionResponseManager:
    """
    Менеджер для отправки и контроля кастомных сообщений-индикаторов
    в ответ на взаимодействия Discord, а также для отправки персональных уведомлений.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        logger: logging.Logger,
        account_data_manager: IAccountDataManager
    ):
        self.bot = bot
        self.logger = logger
        self.account_data_manager = account_data_manager

    async def send_thinking_message(self, interaction: discord.Interaction) -> discord.Message:
        """
        Отправляет кастомное "думает..." сообщение как ответ на интеракцию.
        """
        message_content = "⚙️ Обрабатываю ваш запрос..."

        if not interaction.response.is_done():
            await interaction.response.send_message(message_content, ephemeral=True)
            message = await interaction.original_response()
            self.logger.info(f"Отправлено кастомное сообщение-индикатор для {interaction.user.name}.")
            return message
        else:
            self.logger.warning("Interaction.response уже был завершен. Отправляю индикатор через followup.")
            message = await interaction.followup.send(message_content, ephemeral=True, wait=True)
            return message

    async def complete_thinking_message(self, message: discord.Message, delete_delay: int = 0):
        """
        Удаляет или редактирует сообщение-индикатор после завершения обработки.
        """
        try:
            # Используем edit вместо delete, так как delete_after не всегда работает с ephemeral
            await message.edit(content="✅ Готово!", view=None, embed=None, delete_after=1.5)
            self.logger.info(f"Сообщение-индикатор ID {message.id} отредактировано и будет удалено.")
        except discord.NotFound:
            self.logger.warning(f"Сообщение-индикатор ID {message.id} не найдено для удаления/редактирования.")
        except Exception as e:
            self.logger.error(f"Ошибка при попытке удалить/редактировать сообщение-индикатор ID {message.id}: {e}", exc_info=True)

    async def send_personal_notification_message(self, interaction: discord.Interaction, message: str):
        """
        Отправляет эфемерное сообщение-уведомление пользователю.
        """
        user = interaction.user
        try:
            # Мы больше не пытаемся найти канал, а просто отвечаем на интеракцию
            if interaction.response.is_done():
                # Если уже был ответ (например, "Думаю..."), используем followup
                await interaction.followup.send(message, ephemeral=True)
            else:
                # Если это первый ответ, используем response
                await interaction.response.send_message(message, ephemeral=True)

            self.logger.info(f"Персональное уведомление '{message}' отправлено {user.name}.")
        except Exception as e:
            self.logger.error(f"Не удалось отправить персональное уведомление {user.name}: {e}", exc_info=True)
