# game_server/app_discord_bot/app/cogs/system/load_world_static.py
# Version: 0.003 # Incrementing version

import discord
from discord.ext import commands
import inject
import logging

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.app.services.world_location.game_world_data_loader_service import GameWorldDataLoaderService


class LoadWorldStatic(commands.Cog):
    """
    Команды для загрузки статических данных игрового мира.
    Доступны только администраторам.
    """
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, game_world_data_loader_service: GameWorldDataLoaderService):
        self.bot = bot
        self._game_world_data_loader_service = game_world_data_loader_service
        logger.info("✅ Cog LoadWorldStatic инициализирован.")

    @commands.command(name="load_world_static")
    @commands.is_owner() # Или commands.has_permissions(administrator=True)
    async def load_world_static_command(self, ctx: commands.Context):
        """
        Обработчик текстовой команды Discord для загрузки статических данных игрового мира.
        Использование: !load_world_static
        """
        # Отправляем временное сообщение, чтобы показать, что бот "думает"
        # ephemeral=True делает его видимым только для пользователя
        thinking_message = await ctx.send("⏳ Загружаю статические данные мира... Пожалуйста, подождите.", ephemeral=True)
        logger.info(f"Админ-команда '!load_world_static' вызвана пользователем {ctx.author.id}.")

        try:
            await self._game_world_data_loader_service.load_world_data_from_backend()
            # Редактируем временное сообщение с результатом
            await thinking_message.edit(content="✅ Загрузка статических данных игрового мира успешно завершена.")
            logger.info(f"Админ-команда '!load_world_static' успешно выполнена для пользователя {ctx.author.id}.")
        except Exception as e:
            logger.error(f"Ошибка при выполнении команды '!load_world_static' для пользователя {ctx.author.id}: {e}", exc_info=True)
            # Редактируем временное сообщение с ошибкой
            await thinking_message.edit(
                content=f"❌ Произошла ошибка при загрузке статических данных мира: {e}. Проверьте логи."
            )
        finally:
            # Удаляем сообщение команды администратора через 60 секунд (если оно не было удалено ранее)
            if ctx.message:
                await ctx.message.delete(delay=60)


    @load_world_static_command.error
    async def load_world_static_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.NotOwner):
            # Если бот не может отправить ephemeral, отправляем обычное сообщение
            try:
                await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            except discord.Forbidden:
                await ctx.send("У вас нет прав для использования этой команды.")
        elif isinstance(error, commands.MissingPermissions):
            try:
                await ctx.send("У вас нет необходимых разрешений для использования этой команды.", ephemeral=True)
            except discord.Forbidden:
                await ctx.send("У вас нет необходимых разрешений для использования этой команды.")
        else:
            logger.error(f"Неизвестная ошибка в команде 'load_world_static': {error}", exc_info=True)
            try:
                await ctx.send("Произошла непредвиденная ошибка при выполнении команды.", ephemeral=True)
            except discord.Forbidden:
                await ctx.send("Произошла непредвиденная ошибка при выполнении команды.")
