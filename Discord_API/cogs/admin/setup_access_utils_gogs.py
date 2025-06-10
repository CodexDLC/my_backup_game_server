
from discord.ext import commands

from Discord_API.discord_functions.utils.world_setup_gogs.setup_access_utils import update_guild_access
from Discord_API.config.logging.logging_setup import logger




class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="update_access", description="Обновить права доступа каналов и категорий на сервере.")
    @commands.has_permissions(administrator=True) # Требует прав администратора Discord
    async def update_access_command(self, ctx: commands.Context):
        """
        Команда Discord для запуска обновления прав доступа.
        """
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ Эта команда может быть выполнена только на сервере Discord.")
            return

        await ctx.send("⚡ Запускаю обновление прав доступа Discord в соответствии с настройками game_server. Это может занять некоторое время...")
        
        try:
            await update_guild_access(guild) # Вызываем нашу отдельную оркестратор-функцию
            await ctx.send("✅ Обновление прав доступа успешно завершено!")
        except Exception as e:
            # Ошибка уже логируется внутри update_guild_access, 
            # здесь просто отправляем общее сообщение пользователю
            await ctx.send(f"❌ Произошла ошибка при обновлении прав доступа. Пожалуйста, проверьте логи бота для деталей. Ошибка: `{e}`")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))